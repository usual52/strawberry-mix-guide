import streamlit as st
import pandas as pd
import difflib

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="딸기 농약 혼용 검색기", page_icon="🍓", layout="centered")

st.title("🍓 딸기 농약 혼용 가부 검색기")
st.markdown("청년농들을 위한 안전 방제 가이드입니다. 약제명을 입력하고 혼용 가능 여부를 확인하세요.")

# 2. 데이터 로드 (캐싱하여 접속 속도 향상)
@st.cache_data
def load_data():
    df_db = pd.read_excel('20261012_농약저항성정보 목록_딸기.xlsx', header=2)
    df_db['검색용_상표명'] = df_db['상표명'].astype(str).str.replace(' ', '', regex=False).str.split('(').str[0]
    db_dict = df_db.drop_duplicates(subset=['검색용_상표명']).set_index('검색용_상표명')
    
    df_mix = pd.read_excel('딸기_혼용정보_데이터정리_팜한농_신젠타코리아_한국삼공 .xlsx')
    return db_dict, df_mix

try:
    db_dict, df_mix = load_data()
    registered_names = db_dict.index.tolist()
except Exception as e:
    st.error("데이터 파일을 불러오지 못했습니다. 엑셀 파일이 같은 폴더에 있는지 확인해주세요.")
    st.stop()

# 3. 사용자 입력 UI
col1, col2 = st.columns(2)
with col1:
    drug1_input = st.text_input("첫 번째 약제명", placeholder="예: 스포르곤")
with col2:
    drug2_input = st.text_input("두 번째 약제명", placeholder="예: 미래빛")

# 4. 검색 및 판별 로직
if st.button("혼용 확인하기", type="primary", use_container_width=True):
    if not drug1_input or not drug2_input:
        st.warning("두 약제의 이름을 모두 입력해주세요.")
    else:
        with st.spinner('데이터를 대조 중입니다...'):
            drug1_clean = drug1_input.replace(' ', '').split('(')[0]
            drug2_clean = drug2_input.replace(' ', '').split('(')[0]
            
            corrected_1, corrected_2 = drug1_clean, drug2_clean
            err_msgs = []
            
            # 오타 교정
            if drug1_clean not in registered_names:
                similar = difflib.get_close_matches(drug1_clean, registered_names, n=1, cutoff=0.5)
                if similar:
                    corrected_1 = similar[0]
                    err_msgs.append(f"'{drug1_clean}' ➔ **{corrected_1}**(으)로 교정하여 검색합니다.")
                else:
                    st.error(f"❌ '{drug1_input}'을(를) 목록에서 찾을 수 없습니다.")
                    st.stop()
                    
            if drug2_clean not in registered_names:
                similar = difflib.get_close_matches(drug2_clean, registered_names, n=1, cutoff=0.5)
                if similar:
                    corrected_2 = similar[0]
                    err_msgs.append(f"'{drug2_clean}' ➔ **{corrected_2}**(으)로 교정하여 검색합니다.")
                else:
                    st.error(f"❌ '{drug2_input}'을(를) 목록에서 찾을 수 없습니다.")
                    st.stop()

            if err_msgs:
                for msg in err_msgs:
                    st.info(msg)
            
            # 성분 및 작용기작 추출
            info1, info2 = db_dict.loc[corrected_1], db_dict.loc[corrected_2]
            ing1, ing2 = str(info1['품목명']).split(' ')[0], str(info2['품목명']).split(' ')[0]
            mech1, mech2 = str(info1['작용기작']), str(info2['작용기작'])
            
            # 혼용 가부 판별
            match_result = "정보 없음 (소량 테스트 권장)"
            for idx, row in df_mix.iterrows():
                base = str(row['제품명']).replace(' ', '').split('(')[0]
                targets = []
                if pd.notna(row['살균제']) and str(row['살균제']).strip() != '-':
                    targets.extend([x.replace(' ', '').split('(')[0] for x in str(row['살균제']).split(',')])
                if pd.notna(row['살충제']) and str(row['살충제']).strip() != '-':
                    targets.extend([x.replace(' ', '').split('(')[0] for x in str(row['살충제']).split(',')])
                    
                if (base == corrected_1 and corrected_2 in targets) or (base == corrected_2 and corrected_1 in targets):
                    match_result = row['혼용가부']
                    break

            # 결과 출력
            st.divider()
            st.subheader("검색 결과")
            st.write(f"- **{corrected_1}** (성분: {ing1} / 작용기작: {mech1})")
            st.write(f"- **{corrected_2}** (성분: {ing2} / 작용기작: {mech2})")
            
            if match_result == '○' or match_result == 'O':
                st.success(f"✅ 혼용 가부: **가능 (O)**")
            elif match_result == 'X':
                st.error(f"❌ 혼용 가부: **불가 (X)**")
            elif match_result == '△' or match_result == 'A':
                st.warning(f"⚠️ 혼용 가부: **주의 (△)** - 기준량 엄수 및 혼용 즉시 사용")
            else:
                st.info(f"❓ 혼용 가부: **{match_result}** - 데이터가 없습니다. 사용 전 소량 테스트를 권장합니다.")
            
            # 작용기작 경고
            if mech1 != 'nan' and mech1 == mech2:
                st.error(f"🚨 [경고] 두 약제는 작용기작({mech1})이 동일합니다. 약효 저하 및 내성 우려가 있으므로 혼용을 피하세요.")
