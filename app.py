import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บหน้าตาแบบกว้าง
st.set_page_config(page_title="ACS CPE Load Dashboard", layout="wide")

st.title("📊 ระบบวิเคราะห์ข้อมูล Periodic Inform & CPE Load")
st.markdown("---")

# 1. ฟังก์ชันดึงข้อมูลจาก Google Sheets (แปลงลิงก์เป็น CSV Export)
@st.cache_data(ttl=600)  # ดึงข้อมูลใหม่ทุกๆ 10 นาที
def load_data():
    sheet_id = "1J_bihc7QJiD_ZHa1Xv8P7ROld0ZnNRv8-ubqV8L_kR8"
    gid = "827997903"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    df = pd.read_csv(url)
    
    # กำหนดหัวคอลัมน์ให้ตรงกับโจทย์ของคุณ (ปรับชื่อให้ตรงกับหน้างานจริงหากจำเป็น)
    # สมมติ Column B = 'ProductClass', Column Q = 'PeriodicInform', Column R = 'CpeCount'
    # โค้ดนี้ใช้การระบุตำแหน่งคอลัมน์จากตำแหน่ง Index (0-based) เผื่อชื่อหัวแถวเปลี่ยน
    df.columns.values[1] = 'ProductClass'    # Column B
    df.columns.values[16] = 'PeriodicInform' # Column Q
    df.columns.values[17] = 'CpeCount'       # Column R
    
    # คลีนข้อมูลตัวเลข
    df['CpeCount'] = pd.to_numeric(df['CpeCount'], errors='coerce').fillna(0)
    df['PeriodicInform'] = df['PeriodicInform'].astype(str)
    df['ProductClass'] = df['ProductClass'].astype(str)
    
    return df

try:
    df = load_data()

    # 2. ส่วนควบคุม (Global Filter ด้านซ้ายหรือด้านบน)
    product_list = ["ทั้งหมด"] + sorted(df['ProductClass'].unique().tolist())
    selected_product = st.selectbox("🔍 เลือกรุ่นอุปกรณ์ (ProductClass - Column B):", product_list)

    # กรองข้อมูลตามที่เลือก
    if selected_product != "ทั้งหมด":
        filtered_df = df[df['ProductClass'] == selected_product]
    else:
        filtered_df = df

    # 3. คำนวณสรุปค่า KPIs
    total_cpe = int(filtered_df['CpeCount'].sum())
    
    # หาช่วงเวลาที่ Peak ที่สุด
    peak_group = filtered_df.groupby('PeriodicInform')['CpeCount'].sum()
    if not peak_group.empty:
        peak_interval = peak_group.idxmax()
    else:
        peak_interval = "N/A"

    # แสดงผล KPI Cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🔢 รวมจำนวน CPE ทั้งระบบ (ตามตัวกรอง)", value=f"{total_cpe:,} Devices")
    with col2:
        st.metric(label="🔥 รอบเวลาที่มี Load สูงสุด (Peak Interval)", value=f"{peak_interval}")

    st.markdown("---")

    # 4. แสดงกราฟหลัก Stacked Bar Chart
    st.subheader("📈 ปริมาณ Load แยกตามช่วงเวลา (Periodic Inform) และรุ่นอุปกรณ์")
    
    # จัดกลุ่มเพื่อวาดกราฟ
    chart_data = filtered_df.groupby(['PeriodicInform', 'ProductClass'])['CpeCount'].sum().reset_index()
    
    fig = px.bar(
        chart_data, 
        x='PeriodicInform', 
        y='CpeCount', 
        color='ProductClass',
        title="จำนวนอุปกรณ์ CPE แยกตามรอบเวลาส่งสัญญาณ",
        labels={'PeriodicInform': 'เวลา Periodic Inform (Column Q)', 'CpeCount': 'จำนวน CPE Device (Column R)'},
        template="plotly_white"
    )
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig, use_container_width=True)

    # 5. แสดงตารางสรุปด้านล่าง
    st.subheader("📋 ตารางสรุปอันดับปริมาณรุ่นอุปกรณ์ (Top ProductClass)")
    summary_table = filtered_df.groupby('ProductClass')['CpeCount'].sum().reset_index()
    summary_table = summary_table.sort_values(by='CpeCount', ascending=False).reset_index(drop=True)
    st.dataframe(summary_table, use_container_width=True)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลหรือประมวลผล: {e}")
    st.info("โปรดตรวจสอบสิทธิ์การเข้าถึงลิงก์ Google Sheets ว่าเปิดเป็น 'ทุกคนที่มีลิงก์อ่านได้' (Public/Anyone with link) แล้วหรือยัง")
