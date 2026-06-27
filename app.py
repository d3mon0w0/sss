import os
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io

# ---------- Инициализация Firebase ----------
if not firebase_admin._apps:
    key_content = os.getenv("FIREBASE_KEY")

    if key_content:
        cred_dict = json.loads(key_content)
        cred = credentials.Certificate(cred_dict)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
    else:
        st.error("❌ Ошибка: Ключ Firebase не найден!")
        st.stop()

    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------- Настройка страницы ----------
st.set_page_config(
    page_title="VR/AR в обучении",
    page_icon="🥽",
    layout="centered"
)

# ---------- Стили ----------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #e2e8f0;
    }
    
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px 0 10px 0;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { text-shadow: 0 0 20px rgba(102, 126, 234, 0.3); }
        to { text-shadow: 0 0 40px rgba(118, 75, 162, 0.6); }
    }
    
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #a78bfa;
        margin: 10px 0 15px 0;
        display: flex;
        align-items: center;
        gap: 10px;
        border-bottom: 2px solid rgba(167, 139, 250, 0.2);
        padding-bottom: 10px;
    }
    
    .question-label {
        color: #cbd5e1;
        font-weight: 500;
        font-size: 1.05rem;
        margin-bottom: 8px;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 14px !important;
        border: none !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(118, 75, 162, 0.5) !important;
        filter: brightness(1.1);
    }
    
    .success-message {
        background: linear-gradient(135deg, #10b981, #059669);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 20px;
        animation: slideIn 0.5s ease;
    }
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    .error-message {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        font-size: 1.1rem;
        margin-top: 20px;
    }
    .error-message a {
        color: #93c5fd !important;
        text-decoration: underline !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 15px !important;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .block-container {
        max-width: 800px !important;
        padding: 2rem !important;
    }
    
    /* Кнопки переключения */
    .toggle-buttons {
        display: flex;
        gap: 15px;
        justify-content: center;
        margin: 20px 0 30px 0;
    }
    .toggle-btn {
        padding: 12px 30px;
        border-radius: 12px;
        border: 2px solid rgba(167, 139, 250, 0.3);
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        background: rgba(255,255,255,0.05);
        color: #94a3b8;
        flex: 1;
        max-width: 300px;
        text-align: center;
    }
    .toggle-btn:hover {
        background: rgba(167, 139, 250, 0.1);
        border-color: #a78bfa;
        color: #c4b5fd;
    }
    .toggle-btn.active {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        border-color: #667eea;
    }
    
    /* Убираем все разделители */
    hr {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Состояние ----------
if "mode" not in st.session_state:
    st.session_state.mode = "survey"

# ---------- Заголовок ----------
st.markdown('<div class="main-title">🥽 VR/AR в обучении</div>', unsafe_allow_html=True)

# ---------- Кнопки переключения ----------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("📝 Пройти анкетирование", use_container_width=True, type="primary" if st.session_state.mode == "survey" else "secondary"):
            st.session_state.mode = "survey"
            st.rerun()
    with btn_col2:
        if st.button("📊 Аналитический дашборд", use_container_width=True, type="primary" if st.session_state.mode == "dashboard" else "secondary"):
            st.session_state.mode = "dashboard"
            st.rerun()

st.markdown('<div style="margin: 10px 0 20px 0;"></div>', unsafe_allow_html=True)

# =====================================================
# РЕЖИМ: АНКЕТИРОВАНИЕ
# =====================================================
if st.session_state.mode == "survey":
    
    with st.form("survey_form", clear_on_submit=True):
        
        # ====== РАЗДЕЛ 1 ======
        st.markdown('<div class="section-title">📋 Блок 1: О вас</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="question-label">1. Ваш возраст</div>', unsafe_allow_html=True)
        age = st.number_input("Возраст", min_value=14, max_value=80, value=20, step=1, label_visibility="collapsed")
        
        st.markdown('<div class="question-label">2. Ваш пол</div>', unsafe_allow_html=True)
        gender = st.radio("Пол", ["Мужской", "Женский", "Предпочитаю не указывать"], horizontal=True, label_visibility="collapsed")
        
        st.markdown('<div class="question-label">3. Ваш род занятий / социальный статус</div>', unsafe_allow_html=True)
        education = st.selectbox("Род занятий", ["Школьник", "Студент", "Работаю", "Временно не работаю", "Другое"], index=1, label_visibility="collapsed")
        
        st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
        
        # ====== РАЗДЕЛ 2 ======
        st.markdown('<div class="section-title">🎮 Блок 2: Опыт использования VR/AR</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="question-label">4. Имели ли вы опыт использования VR/AR?</div>', unsafe_allow_html=True)
        vr_experience = st.radio("Опыт VR/AR", ["Да, активно использую", "Пробовал(а) пару раз", "Нет, но интересно", "Нет и не интересно"], label_visibility="collapsed")
        
        st.markdown('<div class="question-label">5. Какие устройства вы используете или хотели бы использовать?</div>', unsafe_allow_html=True)
        device_options = ["VR-шлем (Oculus, Vive)", "AR-очки (HoloLens)", "Смартфон (ARKit/ARCore)", "ПК симуляторы", "Консоли (PSVR)", "Другое"]
        device_type = st.multiselect("Устройства", device_options, label_visibility="collapsed")
        
        device_other = ""
        if "Другое" in device_type:
            device_other = st.text_input("Укажите ваш вариант:", placeholder="Например: специализированное оборудование...", key="device_other_input")
        
        st.markdown('<div class="question-label">6. Как часто вы используете VR/AR в обучении?</div>', unsafe_allow_html=True)
        usage_frequency = st.radio("Частота", ["Ежедневно", "Несколько раз в неделю", "Несколько раз в месяц", "Редко", "Вообще не использую"], label_visibility="collapsed")
        
        st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
        
        # ====== РАЗДЕЛ 3 ======
        st.markdown('<div class="section-title">📊 Блок 3: Оценка эффективности</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="question-label">7. Оцените доступность VR/AR-оборудования для использования в обучении (1-10)</div>', unsafe_allow_html=True)
        accessibility = st.slider("Доступность", 1, 10, 5, label_visibility="collapsed")
        
        st.markdown('<div class="question-label">8. Оцените эффективность VR/AR-технологий для улучшения образовательного процесса (1-10)</div>', unsafe_allow_html=True)
        effectiveness = st.slider("Эффективность", 1, 10, 6, label_visibility="collapsed")
        
        st.markdown('<div class="question-label">9. Оцените ваш личный интерес к использованию VR/AR в обучении (1-10)</div>', unsafe_allow_html=True)
        interest = st.slider("Интерес", 1, 10, 7, label_visibility="collapsed")
        
        st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
        
        # ====== РАЗДЕЛ 4 ======
        st.markdown('<div class="section-title">🚀 Блок 4: Влияние и будущее</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="question-label">10. Как VR/AR влияет на усвоение сложных тем?</div>', unsafe_allow_html=True)
        learning_impact = st.radio("Влияние", [
            "Значительно улучшает понимание материала", 
            "Немного помогает в изучении", 
            "Не влияет на усвоение", 
            "Затрудняет восприятие информации"
        ], label_visibility="collapsed")
        
        st.markdown('<div class="question-label">11. С какими барьерами вы сталкиваетесь при использовании VR/AR?</div>', unsafe_allow_html=True)
        barrier_options = [
            "Высокая стоимость оборудования",
            "Недостаток образовательного контента",
            "Технические сложности",
            "Отсутствие времени на освоение",
            "Недостаток навыков у преподавателей",
            "Другое"
        ]
        barriers = st.multiselect("Барьеры", barrier_options, label_visibility="collapsed")
        
        barriers_other = ""
        if "Другое" in barriers:
            barriers_other = st.text_input("Укажите ваш вариант:", placeholder="Например: отсутствие доступа к интернету...", key="barriers_other_input")
        
        st.markdown('<div class="question-label">12. Готовы ли вы к массовому внедрению VR/AR в образование?</div>', unsafe_allow_html=True)
        future_readiness = st.radio("Готовность", [
            "Полностью готов, это необходимо", 
            "Скорее да, но нужна адаптация", 
            "Скорее нет, есть сомнения", 
            "Категорически против"
        ], label_visibility="collapsed")
        
        st.markdown('<div class="question-label">13. Ваш комментарий или идеи по улучшению VR/AR в обучении</div>', unsafe_allow_html=True)
        comment = st.text_area("Комментарий", placeholder="Поделитесь своим мнением...", label_visibility="collapsed")
        
        # ====== Кнопка отправки ======
        submitted = st.form_submit_button("✨ Отправить анкету")
        
        if submitted:
            if not device_type:
                st.warning("⚠️ Пожалуйста, выберите хотя бы одно устройство (вопрос 5)")
            else:
                all_devices = [d for d in device_type if d != "Другое"]
                if "Другое" in device_type and device_other.strip():
                    all_devices.append(device_other.strip())
                elif "Другое" in device_type and not device_other.strip():
                    all_devices.append("Другое (не указано)")
                
                all_barriers = [b for b in barriers if b != "Другое"]
                if "Другое" in barriers and barriers_other.strip():
                    all_barriers.append(barriers_other.strip())
                elif "Другое" in barriers and not barriers_other.strip():
                    all_barriers.append("Другое (не указано)")
                
                doc_data = {
                    "age": int(age),
                    "gender": gender,
                    "education": education,
                    "vr_experience": vr_experience,
                    "device_type": all_devices,
                    "usage_frequency": usage_frequency,
                    "accessibility": int(accessibility),
                    "effectiveness": int(effectiveness),
                    "interest": int(interest),
                    "learning_impact": learning_impact,
                    "barriers": all_barriers,
                    "future_readiness": future_readiness,
                    "comment": comment,
                    "timestamp": datetime.utcnow()
                }
                
                try:
                    db.collection("vr_ar_survey").add(doc_data)
                    st.markdown('<div class="success-message">✅ Анкета успешно отправлена! Спасибо за участие!</div>', unsafe_allow_html=True)
                    st.balloons()
                except Exception as e:
                    error_msg = str(e)
                    if "SERVICE_DISABLED" in error_msg or "PermissionDenied" in error_msg:
                        st.markdown("""
                        <div class="error-message">
                            ⚠️ Ошибка: Firestore API не включен<br><br>
                            Перейдите по ссылке и включите API:<br>
                            <a href="https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=using-vr-or-ar-in-education" target="_blank">
                                https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=using-vr-or-ar-in-education
                            </a>
                            <br><br>
                            После включения подождите 1-2 минуты и отправьте анкету снова.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ Ошибка: {e}")

# =====================================================
# РЕЖИМ: АНАЛИТИЧЕСКИЙ ДАШБОРД
# =====================================================
else:
    st.markdown('<h2 style="text-align: center; color: #a78bfa;">📊 Аналитический дашборд</h2>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #94a3b8; margin-bottom: 30px;">Режим преподавателя — анализ данных опроса по VR/AR в обучении</p>', unsafe_allow_html=True)
    
    try:
        docs = db.collection("vr_ar_survey").stream()
        data = [doc.to_dict() for doc in docs]
    except Exception as e:
        error_msg = str(e)
        if "SERVICE_DISABLED" in error_msg or "PermissionDenied" in error_msg:
            st.markdown("""
            <div class="error-message">
                ⚠️ Ошибка: Firestore API не включен<br><br>
                Перейдите по ссылке и включите API:<br>
                <a href="https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=using-vr-or-ar-in-education" target="_blank">
                    https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=using-vr-or-ar-in-education
                </a>
                <br><br>
                После включения подождите 1-2 минуты.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"⚠️ Ошибка: {e}")
    else:
        if not data:
            st.info("📭 В базе данных пока нет ответов.")
        else:
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
            
            COLUMN_NAMES = {
                "age": "Возраст", "gender": "Пол", "education": "Образование",
                "vr_experience": "Опыт VR/AR", "device_type": "Устройства",
                "usage_frequency": "Частота использования", "accessibility": "Доступность",
                "effectiveness": "Эффективность", "interest": "Интерес",
                "learning_impact": "Влияние на обучение", "barriers": "Барьеры",
                "future_readiness": "Готовность к внедрению", "comment": "Комментарий",
                "timestamp": "Время"
            }
            df_russian = df.rename(columns=COLUMN_NAMES)
            
            # Ключевые показатели
            st.subheader("📈 Ключевые показатели")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Всего", f"{len(df)}")
            with col2:
                st.metric("📊 Доступность", f"{df['accessibility'].mean():.1f}/10")
            with col3:
                st.metric("📊 Эффективность", f"{df['effectiveness'].mean():.1f}/10")
            with col4:
                st.metric("📊 Интерес", f"{df['interest'].mean():.1f}/10")
            
            st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
            
            # Демография
            st.subheader("👤 Демографический портрет")
            col1, col2 = st.columns(2)
            
            with col1:
                gender_counts = df['gender'].value_counts().reset_index()
                gender_counts.columns = ['Пол', 'Количество']
                fig = px.pie(gender_counts, names='Пол', values='Количество', title='Распределение по полу', color_discrete_sequence=['#6366f1', '#ec4899', '#94a3b8'], hole=0.3)
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                fig.update_traces(marker=dict(line=dict(color='#0f0c29', width=2)))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.histogram(df, x='age', title='Возрастное распределение', labels={'age': 'Возраст'}, color_discrete_sequence=['#667eea'], nbins=20)
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                fig.update_xaxes(showgrid=True, gridcolor='#334155')
                fig.update_yaxes(showgrid=True, gridcolor='#334155')
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
            
            # Оценки
            st.subheader("🎯 Основные оценки")
            fig = px.box(df[['accessibility', 'effectiveness', 'interest']], title='Распределение оценок', labels={'value': 'Оценка', 'variable': 'Параметр'}, color_discrete_sequence=['#667eea', '#a78bfa', '#ec4899'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            fig.update_xaxes(showgrid=True, gridcolor='#334155')
            fig.update_yaxes(showgrid=True, gridcolor='#334155')
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
            
            # Влияние
            col1, col2 = st.columns(2)
            
            with col1:
                impact_counts = df['learning_impact'].value_counts().reset_index()
                impact_counts.columns = ['Влияние', 'Количество']
                fig = px.bar(impact_counts, x='Влияние', y='Количество', title='Влияние на усвоение материала', color_discrete_sequence=['#34d399'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                fig.update_xaxes(showgrid=True, gridcolor='#334155')
                fig.update_yaxes(showgrid=True, gridcolor='#334155')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                readiness_counts = df['future_readiness'].value_counts().reset_index()
                readiness_counts.columns = ['Готовность', 'Количество']
                fig = px.pie(readiness_counts, names='Готовность', values='Количество', title='Готовность к внедрению', color_discrete_sequence=['#34d399', '#fbbf24', '#f87171', '#ef4444'], hole=0.3)
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                fig.update_traces(marker=dict(line=dict(color='#0f0c29', width=2)))
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
            
            # Барьеры
            st.subheader("🚧 Основные барьеры")
            barriers_exploded = df.explode('barriers')
            barrier_counts = barriers_exploded['barriers'].value_counts().reset_index()
            barrier_counts.columns = ['Барьер', 'Количество']
            fig = px.bar(barrier_counts, x='Количество', y='Барьер', title='Самые частые барьеры', color='Количество', color_continuous_scale=['#6366f1', '#ec4899'], orientation='h')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            fig.update_xaxes(showgrid=True, gridcolor='#334155')
            fig.update_yaxes(showgrid=True, gridcolor='#334155')
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
            
            # Устройства
            st.subheader("🖥️ Используемые устройства")
            devices_exploded = df.explode('device_type')
            device_counts = devices_exploded['device_type'].value_counts().reset_index()
            device_counts.columns = ['Устройство', 'Количество']
            fig = px.bar(device_counts, x='Количество', y='Устройство', title='Популярность устройств', color='Количество', color_continuous_scale=['#667eea', '#a78bfa'], orientation='h')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            fig.update_xaxes(showgrid=True, gridcolor='#334155')
            fig.update_yaxes(showgrid=True, gridcolor='#334155')
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
            
            # Таблица
            st.subheader("📋 Все ответы")
            cols_to_show = ['Возраст', 'Пол', 'Образование', 'Доступность', 'Эффективность', 'Интерес']
            st.dataframe(df_russian[cols_to_show], use_container_width=True)
            
            st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
            
            # Экспорт
            st.subheader("📥 Экспорт данных")
            col1, col2 = st.columns(2)
            current_time = datetime.now().strftime("%Y%m%d_%H%M")
            
            with col1:
                csv = df_russian.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label="📄 Скачать CSV", data=csv, file_name=f"vr_ar_survey_{current_time}.csv", mime="text/csv")
            
            with col2:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_russian.to_excel(writer, index=False, sheet_name='Ответы')
                excel_buffer.seek(0)
                st.download_button(label="📊 Скачать Excel", data=excel_buffer.getvalue(), file_name=f"vr_ar_survey_{current_time}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")