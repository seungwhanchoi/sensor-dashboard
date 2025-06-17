import streamlit as st
import pandas as pd
import glob
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

st.set_page_config(page_title="Sensor Data Viewer", layout="wide")

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic' 
plt.rcParams['axes.unicode_minus'] = False 
sns.set(font='Malgun Gothic')

# 사이드바 메뉴
with st.sidebar:
    st.title("📊 메뉴")
    menu = st.radio("이동할 메뉴를 선택하세요", ["main", "Data Analysis"])

# 1. Load Error Lot list
def load_error_lot(file_path):
    df = pd.read_csv(file_path, header=None)
    df.dropna(how="all", inplace=True)
    try:
        pd.to_datetime(df.iloc[0, 0])
    except:
        df = df.iloc[1:]
    df = df.melt(id_vars=[0], var_name="Lot_Index", value_name="Process")
    df.columns = ["Date", "Lot_Index", "Process"]
    df.dropna(subset=["Process"], inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date"], inplace=True)
    df["Process"] = df["Process"].astype(int).astype(str)
    return df

# 2. Load sensor CSVs from directory
def load_sensor_data(base_dir):
    all_files = sorted(glob.glob(f"{base_dir}/kemp-abh-sensor-*.csv"))
    data_map = {}
    for file in all_files:
        try:
            date_str = Path(file).stem.split("-")[-1]
            date = pd.to_datetime(date_str, format="%Y.%m.%d")
            df = pd.read_csv(file)
            df["source_file"] = file
            data_map[date.date()] = df
        except:
            continue
    return data_map

# 통합 경로 설정
base_folder = "C:/Users/chltm/Downloads/Dataset_장비이상 조기탐지 AI 데이터셋/data/5공정_180sec"
error_lot_file = f"{base_folder}/Error Lot list.csv"
sensor_data_folder = base_folder

# 페이지 분기 처리
if menu == "main":
    st.title("메인 페이지")
    st.image("https://cdn.pixabay.com/photo/2016/03/09/09/30/industrial-1245714_1280.jpg", caption="열풍 건조 공정")
    st.markdown("이 시스템은 장비 이상 탐지 및 공정 데이터를 분석하는 대시보드입니다.")

elif menu == "Data Analysis":
    st.title("Data Analysis")
    error_lot_df = load_error_lot(error_lot_file)
    sensor_data_dict = load_sensor_data(sensor_data_folder)

    available_dates = sorted(sensor_data_dict.keys())
    selected_date = st.selectbox("날짜를 선택하세요", available_dates)

    data = sensor_data_dict.get(selected_date)
    error_processes = error_lot_df[error_lot_df["Date"] == pd.to_datetime(selected_date)]["Process"].tolist()

    st.subheader(f"\U0001F4C8 {selected_date} 데이터")
    if data is not None:
        data["Error"] = data["Process"].astype(str).isin(error_processes)
        data["Error"] = data["Error"].map({True: "Error", False: "Normal"})
        filtered = data[data["Error"] == "Error"]

        tab1, tab2, tab3 = st.tabs(["에러 데이터", "정상/이상 분포", "산점도 및 상관관계"])

        with tab1:
            if not filtered.empty:
                st.dataframe(filtered, use_container_width=True)
                st.warning(f"에러 공정(Process): {', '.join(error_processes)}")
            else:
                st.success("에러 없음 (정상 Lot)")

        with tab2:
            col1, col2 = st.columns([1, 2])
            with col1:
                pie_counts = data["Error"].value_counts()
                fig1, ax1 = plt.subplots(figsize=(2.5, 2.5))
                ax1.pie(pie_counts, labels=pie_counts.index, autopct='%1.1f%%', startangle=90)
                ax1.axis('equal')
                st.pyplot(fig1, clear_figure=True, use_container_width=False)

            with col2:
                fig2, axes = plt.subplots(1, 2, figsize=(8, 3))
                sns.kdeplot(data=data, x="Temp", hue="Error", ax=axes[0], fill=True)
                axes[0].set_title("온도 분포")
                axes[0].set_xlabel("Temp")
                axes[0].set_ylabel("")
                sns.kdeplot(data=data, x="Current", hue="Error", ax=axes[1], fill=True)
                axes[1].set_title("전류 분포")
                axes[1].set_xlabel("Current")
                axes[1].set_ylabel("")
                st.pyplot(fig2)

        with tab3:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("#### 온도 vs 전류 산점도")
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                sns.scatterplot(data=data, x="Temp", y="Current", hue="Error", ax=ax3, alpha=0.7)
                ax3.set_xlabel("Temp")
                ax3.set_ylabel("Current")
                ax3.set_title("온도와 전류의 관계")
                st.pyplot(fig3)

            with col2:
                st.markdown("#### 상관관계 매트릭스")
                corr = data[["Temp", "Current"]].corr()
                fig4, ax4 = plt.subplots(figsize=(3.5, 3.5))
                sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax4)
                st.pyplot(fig4)
    else:
        st.error("해당 날짜의 데이터를 찾을 수 없습니다.")
