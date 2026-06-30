"""
Hệ Thống Thẩm Định Tín Dụng Doanh Nghiệp
-----------------------------------------
Ứng dụng Streamlit hỗ trợ phân tích chỉ số tài chính và tự động đề xuất
quyết định cấp tín dụng cho doanh nghiệp dựa trên các tiêu chí: LTV, DSCR,
ROA, ROE và xếp hạng tín dụng nội bộ (CIC).

Run: streamlit run credit_appraisal_app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# ---------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Hệ Thống Thẩm Định Tín Dụng Doanh Nghiệp",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 2. CSS TUỲ CHỈNH
# ---------------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f7f6;
    }
    #MainMenu, footer {visibility: hidden;}

    .main-header {
        padding: 1.2rem 1.5rem;
        background: linear-gradient(135deg, #0056b3 0%, #003d82 100%);
        border-radius: 14px;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 28px;
    }
    .main-header p {
        color: #d6e4f7;
        margin: 4px 0 0 0;
        font-size: 15px;
    }

    div.stButton > button:first-child {
        background-color: #0056b3;
        color: white;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        height: 55px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #003d82;
        transform: translateY(-2px);
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #0056b3;
    }

    .footer-note {
        text-align: center;
        color: #999;
        font-size: 12px;
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 3. HEADER
# ---------------------------------------------------------------------------
st.markdown("""
    <div class="main-header">
        <h1>🏢 HỆ THỐNG THẨM ĐỊNH TÍN DỤNG DOANH NGHIỆP</h1>
        <p>Đánh giá rủi ro, phân tích chỉ số tài chính và tự động đề xuất quyết định phê duyệt khoản vay.</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 4. SIDEBAR - GIỚI THIỆU NGẮN
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("ℹ️ Hướng dẫn sử dụng")
    st.markdown("""
    1. Nhập **hồ sơ tài chính** của doanh nghiệp.
    2. Nhập **phương án vay vốn** và tài sản đảm bảo.
    3. Bấm **Bắt đầu phân tích** để xem kết quả.
    """)
    st.divider()
    st.caption("Ngưỡng đánh giá tham khảo")
    st.markdown("""
    - **LTV** an toàn: ≤ 80%
    - **DSCR** an toàn: ≥ 1.2x
    - **ROA** kỳ vọng: ≥ 3%
    - **ROE** kỳ vọng: ≥ 8%
    """)
    st.divider()
    st.caption("⚙️ Demo / Mục đích minh hoạ — không phải tư vấn tài chính chính thức.")

# ---------------------------------------------------------------------------
# 5. KHU VỰC NHẬP LIỆU
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📊 1. Hồ sơ Tài chính Doanh nghiệp")
        LNST = st.number_input(
            "Lợi nhuận sau thuế năm gần nhất (Triệu VND)",
            value=2000.0, step=100.0
        )
        c1, c2 = st.columns(2)
        with c1:
            ROA = st.number_input("Chỉ số ROA (%)", value=5.0, step=0.1)
        with c2:
            ROE = st.number_input("Chỉ số ROE (%)", value=15.0, step=0.1)

        CIC_DN = st.selectbox(
            "Xếp hạng Tín dụng Nội bộ / CIC",
            [
                "Hạng A (Rất tốt, Rủi ro rất thấp)",
                "Hạng B (Tốt, Rủi ro thấp)",
                "Hạng C (Trung bình, Rủi ro vừa)",
                "Hạng D (Rủi ro cao - Nợ xấu)",
            ],
        )

with col2:
    with st.container(border=True):
        st.subheader("💰 2. Phương án Vay vốn & TSĐB")
        STV = st.number_input("Số tiền đề nghị vay (Triệu VND)", min_value=1.0, value=5000.0, step=100.0)
        TGV = st.number_input("Thời gian vay (Năm)", min_value=0.5, value=3.0, step=0.5)
        LSV = st.number_input("Lãi suất cho vay (%/năm)", min_value=0.0, value=8.5, step=0.1)
        GTTSDB = st.number_input("Giá trị Tài sản đảm bảo (Triệu VND)", min_value=1.0, value=8000.0, step=100.0)

st.write("")

# ---------------------------------------------------------------------------
# 6. XỬ LÝ PHÂN TÍCH
# ---------------------------------------------------------------------------
if st.button("🚀 BẮT ĐẦU PHÂN TÍCH & XÉT DUYỆT", use_container_width=True):

    with st.spinner("Hệ thống đang trích xuất dữ liệu và chạy mô hình rủi ro..."):
        time.sleep(1.0)

        goc_hang_nam = STV / TGV
        lai_hang_nam = STV * (LSV / 100)
        tong_no_hang_nam = goc_hang_nam + lai_hang_nam
        DSCR = LNST / tong_no_hang_nam if tong_no_hang_nam > 0 else float("inf")
        LTV = STV / GTTSDB

        st.divider()
        st.subheader("📈 KẾT QUẢ PHÂN TÍCH CHỈ SỐ")

        col3, col4, col5 = st.columns(3)
        col3.metric(
            "Tỷ lệ cấp tín dụng (LTV)",
            f"{LTV * 100:.2f}%",
            "Mức an toàn: ≤ 80%",
            delta_color="normal" if LTV <= 0.8 else "inverse",
        )
        col4.metric(
            "Hệ số trả nợ (DSCR)",
            f"{DSCR:.2f}x",
            "Mức an toàn: ≥ 1.2x",
            delta_color="normal" if DSCR >= 1.2 else "inverse",
        )
        col5.metric("Nghĩa vụ nợ hàng năm", f"{tong_no_hang_nam:,.0f} Tr VND")

        # --- Biểu đồ trực quan ---
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            gauge_ltv = go.Figure(go.Indicator(
                mode="gauge+number",
                value=LTV * 100,
                title={"text": "LTV (%)"},
                gauge={
                    "axis": {"range": [0, 120]},
                    "bar": {"color": "#0056b3"},
                    "steps": [
                        {"range": [0, 80], "color": "#d4edda"},
                        {"range": [80, 120], "color": "#f8d7da"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 3},
                        "value": 80,
                    },
                },
            ))
            gauge_ltv.update_layout(height=280, margin=dict(t=40, b=10, l=20, r=20))
            st.plotly_chart(gauge_ltv, use_container_width=True)

        with chart_col2:
            gauge_dscr = go.Figure(go.Indicator(
                mode="gauge+number",
                value=DSCR,
                title={"text": "DSCR (x)"},
                gauge={
                    "axis": {"range": [0, max(3, DSCR + 0.5)]},
                    "bar": {"color": "#0056b3"},
                    "steps": [
                        {"range": [0, 1.2], "color": "#f8d7da"},
                        {"range": [1.2, max(3, DSCR + 0.5)], "color": "#d4edda"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 3},
                        "value": 1.2,
                    },
                },
            ))
            gauge_dscr.update_layout(height=280, margin=dict(t=40, b=10, l=20, r=20))
            st.plotly_chart(gauge_dscr, use_container_width=True)

        # --- Bảng tổng hợp dòng tiền vay ---
        with st.expander("📑 Xem chi tiết cơ cấu nghĩa vụ nợ hàng năm"):
            df_debt = pd.DataFrame({
                "Hạng mục": ["Gốc vay/năm", "Lãi vay/năm", "Tổng nghĩa vụ nợ/năm"],
                "Giá trị (Triệu VND)": [goc_hang_nam, lai_hang_nam, tong_no_hang_nam],
            })
            st.dataframe(df_debt, use_container_width=True, hide_index=True)

        st.write("---")

        # ---------------------------------------------------------------
        # 7. QUYẾT ĐỊNH TÍN DỤNG
        # ---------------------------------------------------------------
        st.subheader("📋 QUYẾT ĐỊNH TỪ HỘI ĐỒNG TÍN DỤNG TỰ ĐỘNG")

        if "Hạng D" in CIC_DN:
            st.error("#### ❌ TỪ CHỐI CẤP TÍN DỤNG\n**Lý do:** Doanh nghiệp có lịch sử tín dụng/xếp hạng rủi ro cao (Hạng D).")
        elif LNST <= 0:
            st.error("#### ❌ TỪ CHỐI CẤP TÍN DỤNG\n**Lý do:** Doanh nghiệp đang hoạt động thua lỗ (LNST ≤ 0). Không có nguồn tiền trả nợ.")
        elif LTV > 0.8:
            st.warning(f"#### ⚠️ YÊU CẦU BỔ SUNG TÀI SẢN ĐẢM BẢO\n**Lý do:** Tỷ lệ LTV ({LTV * 100:.2f}%) vượt mức trần 80%. Rủi ro thanh lý tài sản cao.")
        elif DSCR < 1.2:
            st.warning(f"#### ⚠️ YÊU CẦU GIẢM HẠN MỨC HOẶC KÉO DÀI THỜI GIAN VAY\n**Lý do:** Hệ số bù đắp nợ DSCR ({DSCR:.2f}x) thấp hơn 1.2x. Dòng tiền hiện tại tạo áp lực trả nợ lớn.")
        elif ROA < 3.0 or ROE < 8.0:
            st.info("#### ⚠️ PHÊ DUYỆT CÓ ĐIỀU KIỆN\n**Lưu ý:** Khả năng trả nợ an toàn (DSCR đạt) nhưng hiệu quả sinh lời (ROA/ROE) thấp. Yêu cầu chuyên viên kiểm soát chặt chẽ mục đích sử dụng vốn.")
        else:
            st.success("#### ✅ ĐỒNG Ý CẤP TÍN DỤNG\n**Đánh giá:** Hồ sơ xuất sắc. Doanh nghiệp có hiệu quả hoạt động tốt (ROA, ROE cao), khả năng trả nợ an toàn và TSĐB đầy đủ.")
            st.balloons()

st.markdown("<p class='footer-note'>Hệ thống thẩm định tín dụng demo • Xây dựng bằng Streamlit • Không thay thế đánh giá chuyên môn của cán bộ tín dụng</p>", unsafe_allow_html=True)
