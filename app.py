import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------
# 1. การตั้งค่าหน้าเว็บ (Page Configuration)
# ---------------------------------------------------
st.set_page_config(
    page_title="ACS CPE Load Dashboard", 
    page_icon="📡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# 2. ฟังก์ชันดึงและเตรียมข้อมูล (Data Fetching & Cleaning)
# ---------------------------------------------------
@st.cache_data(ttl=600) 
def load_data():
    sheet_id = "1J_bihc7QJiD_ZHa1Xv8P7ROld0ZnNRv8-ubqV8L_kR8"
    gid = "827997903"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    df = pd.read_csv(url)
    
    df.columns.values[1] = 'ProductClass'    # Column B
    df.columns.values[16] = 'PeriodicInform' # Column Q
    df.columns.values[17] = 'CpeCount'       # Column R
    
    df['CpeCount'] = pd.to_numeric(df['CpeCount'], errors='coerce').fillna(0)
    df = df[df['CpeCount'] > 0]
    df['PeriodicInform'] = df['PeriodicInform'].fillna("ไม่ระบุ").astype(str)
    df['ProductClass'] = df['ProductClass'].fillna("ไม่ระบุ").astype(str)
    
    return df

try:
    df = load_data()

    # ---------------------------------------------------
    # 3. แถบเครื่องมือด้านข้าง (Sidebar Controls - UX Improvement)
    # ---------------------------------------------------
    with st.sidebar:
        st.markdown("### ⚙️ ตัวกรองข้อมูล (Filters)")
        st.markdown("เลือกเงื่อนไขเพื่อวิเคราะห์โหลดของระบบ")
        
        product_list = ["ทั้งหมด"] + sorted(df['ProductClass'].unique().tolist())
        selected_product = st.selectbox("📌 เลือกรุ่นอุปกรณ์ (ProductClass):", product_list)

        time_list = ["ทั้งหมด"] + sorted(df['PeriodicInform'].unique().tolist())
        selected_time = st.selectbox("⏱️ เลือกเวลาส่งสัญญาณ (Periodic Inform):", time_list)
        
        st.markdown("---")
        st.caption("อัปเดตข้อมูลอัตโนมัติจาก Google Sheets")

    # กรองข้อมูล
    filtered_df = df.copy()
    if selected_product != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['ProductClass'] == selected_product]
    if selected_time != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['PeriodicInform'] == selected_time]

    # ---------------------------------------------------
    # 4. พื้นที่แสดงผลหลัก (Main Content Area)
    # ---------------------------------------------------
    st.title("📡 ระบบวิเคราะห์โหลด FTTx ACS (CPE Inform)")
    st.markdown("แดชบอร์ดสรุปสถิติรอบการส่งสัญญาณของอุปกรณ์เพื่อการบริหารจัดการ Capacity")
    st.markdown("<br>", unsafe_allow_html=True) # เพิ่มช่องว่างให้หายใจ (Whitespace)

    # --- ส่วนสรุป KPI (Top Metrics) ---
    total_cpe = int(filtered_df['CpeCount'].sum())
    peak_group = filtered_df.groupby('PeriodicInform')['CpeCount'].sum()
    peak_interval = peak_group.idxmax() if not peak_group.empty else "N/A"

    # ใช้ Container ช่วยจัดกรอบให้ดูเป็นสัดส่วน
    kpi_container = st.container(border=True)
    with kpi_container:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total CPEs (จำนวนอุปกรณ์ทั้งหมดในระบบ)", value=f"{total_cpe:,} เครื่อง")
        with col2:
            st.metric(label="Peak Load Interval (รอบเวลาที่มีความหนาแน่นสูงสุด)", value=f"{peak_interval}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ส่วนกราฟ (Main Visualization) ---
    st.markdown("#### 📈 ปริมาณ Load แยกตามช่วงเวลา (Periodic Inform) และรุ่นอุปกรณ์")
    
    chart_data = filtered_df.groupby(['PeriodicInform', 'ProductClass'])['CpeCount'].sum().reset_index()
    total_per_interval = chart_data.groupby('PeriodicInform')['CpeCount'].sum().reset_index()
    
    if not chart_data.empty:
        # ใช้โทนสีระดับมืออาชีพ (Color Sequence)
        fig = px.bar(
            chart_data, 
            x='PeriodicInform', 
            y='CpeCount', 
            color='ProductClass',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={'PeriodicInform': 'เวลา Periodic Inform', 'CpeCount': 'จำนวน CPE', 'ProductClass': 'รุ่นอุปกรณ์'}
        )
        
        fig.update_layout(
            barmode='stack', 
            xaxis={'categoryorder':'total descending'},
            plot_bgcolor='rgba(0,0,0,0)', # ทำให้พื้นหลังกราฟโปร่งใส กลืนไปกับเว็บ
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) # ย้าย Legend ไว้ด้านบน
        )
        
        # ลบเส้นกริดแกน X และทำเส้นกริดแกน Y ให้บางลง
        fig.update_xaxes(showgrid=False, linecolor='lightgrey')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)', linecolor='lightgrey')

        # ปรับ Tooltip เมื่อเอาเมาส์ชี้ให้สวยงาม
        fig.update_traces(hovertemplate='<b>%{x}</b><br>รุ่น: %{data.name}<br>จำนวน: %{y:,} เครื่อง<extra></extra>')

        fig.add_scatter(
            x=total_per_interval['PeriodicInform'], 
            y=total_per_interval['CpeCount'],
            mode='text',
            text=total_per_interval['CpeCount'],
            textposition='top center',
            texttemplate='<b>%{text:,}</b>',
            textfont=dict(size=14), 
            showlegend=False,
            hoverinfo='skip'
        )
        
        max_y = total_per_interval['CpeCount'].max()
        fig.update_layout(yaxis=dict(range=[0, max_y * 1.15]))

        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    else:
        st.info("💡 ไม่พบข้อมูลที่ตรงกับเงื่อนไขการกรองที่คุณเลือกทางด้านซ้ายมือ")

    # --- ส่วนตารางข้อมูล (Data Table) ---
    st.markdown("#### 📋 ตารางสรุปปริมาณอุปกรณ์แยกตามรุ่น (Top Models)")
    if not filtered_df.empty:
        summary_table = filtered_df.groupby('ProductClass')['CpeCount'].sum().reset_index()
        summary_table = summary_table.sort_values(by='CpeCount', ascending=False)
        
        # ใช้ st.dataframe แบบปรับแต่ง UI ให้ตารางสวยงาม
        st.dataframe(
            summary_table, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "ProductClass": st.column_config.TextColumn("รุ่นอุปกรณ์ (ProductClass)", width="medium"),
                "CpeCount": st.column_config.NumberColumn("จำนวนอุปกรณ์รวม (เครื่อง)", format="%d")
            }
        )

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลหรือประมวลผล: {e}")
