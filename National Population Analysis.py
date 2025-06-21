
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pymongo import MongoClient
from sklearn.linear_model import LinearRegression

# MongoDB 연결
def connect_mongodb():
    client = MongoClient("mongodb://localhost:27017")
    db = client["births_deaths_db"]
    coll = db["projections"]
    return coll

# MongoDB에서 데이터 가져오기
def get_data_from_mongodb():
    coll = connect_mongodb()
    data = list(coll.find())
    # ObjectId 변환 (ObjectId는 스트림릿에서 처리하기 어려우므로 문자열로 변환)
    for item in data:
        item['_id'] = str(item['_id'])
    df = pd.DataFrame(data)
    return df

# Streamlit 애플리케이션
st.title("Births and Deaths Visualization")

# MongoDB에서 데이터 로드
df = get_data_from_mongodb()

# 데이터 컬럼명 통일 (MongoDB 데이터와 기존 CSV 데이터 컬럼명을 일치시킴)
df = df.rename(columns={
    'Deaths - Sex: all - Age: all - Variant: estimates': 'deaths',
    'Births - Sex: all - Age: all - Variant: estimates': 'births',
    'Year': 'year',
    'Entity': 'entity'
})

# 사용자 인터페이스: 국가 선택
selected_country = st.selectbox("Select a Country", df['entity'].unique())
filtered_df = df[df['entity'] == selected_country]

# 연도 슬라이더 (최대 연도를 미래로 확장)
min_year, max_year = int(df['year'].min()), int(df['year'].max())
year_range = st.slider("Select Year Range", min_value=min_year, max_value=max_year + 20, value=(min_year, max_year))
selected_start_year, selected_end_year = year_range

# 연도 범위를 벗어나면 예측 데이터 생성
if selected_end_year > max_year:
    # 미래 연도 데이터 생성
    future_years = np.arange(max_year + 1, selected_end_year + 1).reshape(-1, 1)
    
    # 선형 회귀 모델을 사용한 예측
    model = LinearRegression()
    model.fit(filtered_df[['year']], filtered_df['births'])
    future_births = model.predict(future_years)

    # 사망 데이터는 0으로 설정 (필요시 더 정교한 예측 모델 사용 가능)
    future_deaths = np.zeros(len(future_years))

    # 예측 데이터프레임 생성
    future_df = pd.DataFrame({
        'year': future_years.flatten(),
        'births': future_births,
        'deaths': future_deaths,
        'entity': [selected_country] * len(future_years)
    })

    # 기존 데이터와 예측 데이터 결합
    filtered_df = pd.concat([filtered_df, future_df], ignore_index=True)

# 연도 범위로 데이터 필터링
filtered_df = filtered_df[(filtered_df['year'] >= selected_start_year) & (filtered_df['year'] <= selected_end_year)]

# 그래프 생성
if not filtered_df.empty:
    fig, ax = plt.subplots()
    ax.plot(filtered_df['year'], filtered_df['births'], label='Births', color='blue', marker='o')
    ax.plot(filtered_df['year'], filtered_df['deaths'], label='Deaths', color='red', marker='x')
    ax.set_xlabel("Year")
    ax.set_ylabel("Count")
    ax.set_title(f"Births vs Deaths in {selected_country}")
    ax.legend()
    st.pyplot(fig)
else:
    st.warning("No data available for the selected range. Please choose a different range.")
