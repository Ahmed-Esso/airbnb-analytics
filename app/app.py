import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
import os
import base64
from catboost import CatBoostRegressor

# ==================== 1. PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Airbnb Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 2. THEME & COLORS ====================
AIRBNB_COLOR = "#FF385C"
AIRBNB_GRADIENT = f"linear-gradient(135deg, {AIRBNB_COLOR}, #BD1E59)"

# Theme Variables
bg_color = "#FFFFFF"
text_color = "#1a1a2e"
chart_text_color = "#1a1a2e"
card_bg = "#f8fafc"
plotly_template = "plotly_white"
border_color = "rgba(0,0,0,0.08)"
chart_bg = "rgba(0,0,0,0)"
chart_grid_color = "rgba(0,0,0,0.05)"

# ==================== 3. CSS STYLING ====================
st.markdown(f"""
<style>
    #MainMenu, footer, header {{ visibility: hidden; }}

    html, body, .main, .stApp {{
        background-color: {bg_color};
        color: {text_color};
        font-family: 'Circular', -apple-system, sans-serif;
        font-size: 16px;
    }}

    .block-container {{ padding-top: 2rem; }}

    h1, h2, h3, h4 {{ text-align: center !important; font-weight: 700; }}
    h1 {{ font-size: 2.5rem !important; }}
    h2 {{ font-size: 2rem !important; }}
    h3 {{ font-size: 1.75rem !important; }}
    h4 {{ font-size: 1.5rem !important; }}

    /* Header */
    .header-container {{
        background: {AIRBNB_GRADIENT};
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 20px rgba(255, 56, 92, 0.3);
    }}

    /* KPI Cards */
    .kpi-card {{
        background-color: {card_bg};
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border-bottom: 4px solid {AIRBNB_COLOR};
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        height: 100%;
    }}
    .kpi-value {{ font-size: 38px; font-weight: 800; color: {AIRBNB_COLOR}; }}
    .kpi-label {{ font-size: 16px; opacity: 0.7; margin-top: 5px; text-transform: uppercase; font-weight: 600; }}

    /* Prediction Card */
    .prediction-result {{
        background: {AIRBNB_GRADIENT};
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        color: white;
        animation: fadeIn 0.5s ease-in;
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(255, 56, 92, 0.4);
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* Input Styling */
    .stSelectbox, .stNumberInput, .stSlider {{
        background-color: {card_bg};
        border-radius: 10px;
        padding: 10px;
    }}
    
    .stSelectbox label, .stNumberInput label, .stSlider label, .stCheckbox label {{
        font-size: 16px !important;
        font-weight: 600 !important;
        color: {text_color} !important;
    }}
    
    .stCheckbox > label {{
        font-size: 18px !important;
        font-weight: 600 !important;
    }}
    
    /* Button Styling */
    .stButton > button, .stFormSubmitButton > button {{
        background: {AIRBNB_COLOR} !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
    }}
    
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background: #E00B4A !important;
        box-shadow: 0 4px 12px rgba(255, 56, 92, 0.4) !important;
    }}
    
    /* Hide sidebar close button so it stays open */
    [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}
    
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}
    
    button[kind="header"] {{
        display: none !important;
    }}
    
    .js-plotly-plot {{ margin-left: auto; margin-right: auto; }}
</style>
""", unsafe_allow_html=True)

# ==================== 4. INTRO ANIMATION ====================
if "intro_done" not in st.session_state:
    st.session_state.intro_done = False

def show_intro():
    IMAGE_PATH = os.path.join(os.path.dirname(__file__), "airbnb_symbol.svg")
    
    if not os.path.exists(IMAGE_PATH):
        st.error("Image not found! Please ensure 'Airbnb_Symbol_0.svg' is in the same folder as the app.")
        st.session_state.intro_done = True
        return
        
    with open(IMAGE_PATH, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode()

    mime_type = "image/svg+xml" if IMAGE_PATH.endswith(".svg") else "image/png"

    intro = st.empty()
    intro.markdown(f"""
    <style>
        .intro-container {{
            position: fixed; inset: 0;
            background: #FFFFFF;
            display: flex; justify-content: center; align-items: center;
            z-index: 9999;
            animation: fadeOut 0.6s ease-in-out 2.5s forwards;
        }}
        @keyframes fadeOut {{ to {{ opacity: 0; visibility: hidden; }} }}
        
        .intro-image {{
            width: 300px;
            height: auto;
            animation: scaleIn 0.8s ease-out forwards;
        }}
        @keyframes scaleIn {{ from {{ transform: scale(0.5); opacity: 0; }} to {{ transform: scale(1); opacity: 1; }} }}
    </style>
    <div class="intro-container">
        <img src="data:{mime_type};base64,{encoded_image}" class="intro-image" alt="App Logo">
    </div>
    """, unsafe_allow_html=True)
    time.sleep(3)
    intro.empty()
    st.session_state.intro_done = True

if not st.session_state.intro_done:
    show_intro()

# ==================== 5. LOAD DATA & MODEL ====================
@st.cache_data
def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "data", "airbnb_listings_clean.csv")
    return pd.read_csv(data_path)

@st.cache_resource
def load_model():
    try:
        model = CatBoostRegressor()
        model_path = os.path.join(os.path.dirname(__file__), "airbnb_model.cbm")
        model.load_model(model_path)
        return model
    except:
        return None

df = load_data()

# Remove outliers using IQR method (calculated dynamically from data)
Q1 = df['realSum'].quantile(0.25)
Q3 = df['realSum'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - (1.5 * IQR)
upper_bound = Q3 + (1.5 * IQR)

# Filter out outliers from realSum column
df = df[(df['realSum'] >= lower_bound) & (df['realSum'] <= upper_bound)].copy()

# ==================== SIDEBAR FILTERS ====================
with st.sidebar:
    st.markdown("### Filters")
    st.markdown("---")
    
    # City Filter
    st.markdown("#### Cities")
    all_cities = sorted(df['city'].unique())
    selected_cities = st.multiselect(
        "Select cities",
        options=all_cities,
        default=all_cities,
        label_visibility="collapsed"
    )
    
    # Room Type Filter
    st.markdown("#### Room Type")
    all_room_types = sorted(df['room_type'].unique())
    selected_room_types = st.multiselect(
        "Select room types",
        options=all_room_types,
        default=all_room_types,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Price Range Filter
    st.markdown("#### Price Range ($)")
    min_price = int(df['realSum'].min())
    max_price = int(df['realSum'].max())
    # Use actual max after outlier removal (capped at ~490)
    slider_max = max_price
    price_range = st.slider(
        "Select price range",
        min_value=min_price,
        max_value=slider_max,
        value=(min_price, slider_max),
        label_visibility="collapsed"
    )
    
    # Guest Capacity Filter
    st.markdown("#### Guest Capacity")
    min_capacity = int(df['person_capacity'].min())
    max_capacity = int(df['person_capacity'].max())
    capacity_range = st.slider(
        "Select capacity",
        min_value=min_capacity,
        max_value=max_capacity,
        value=(min_capacity, max_capacity),
        label_visibility="collapsed"
    )
    
    # Rating Filter
    st.markdown("#### Minimum Rating")
    min_rating = st.slider(
        "Select minimum rating",
        min_value=0,
        max_value=100,
        value=0,
        label_visibility="collapsed"
    )
    
    # Superhost Filter
    st.markdown("#### Superhost")
    superhost_filter = st.radio(
        "Superhost filter",
        options=["All", "Superhost Only", "Regular Only"],
        index=0,
        label_visibility="collapsed"
    )
    
    # Weekend Filter
    st.markdown("#### Day Type")
    day_filter = st.radio(
        "Day type filter",
        options=["All", "Weekend Only", "Weekday Only"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Reset button
    if st.button("Reset Filters", use_container_width=True):
        st.rerun()

# Apply Filters
filtered_df = df.copy()

if selected_cities:
    filtered_df = filtered_df[filtered_df['city'].isin(selected_cities)]

if selected_room_types:
    filtered_df = filtered_df[filtered_df['room_type'].isin(selected_room_types)]

filtered_df = filtered_df[
    (filtered_df['realSum'] >= price_range[0]) & 
    (filtered_df['realSum'] <= price_range[1])
]

filtered_df = filtered_df[
    (filtered_df['person_capacity'] >= capacity_range[0]) & 
    (filtered_df['person_capacity'] <= capacity_range[1])
]

filtered_df = filtered_df[filtered_df['guest_satisfaction_overall'] >= min_rating]

if superhost_filter == "Superhost Only":
    filtered_df = filtered_df[filtered_df['host_is_superhost'] == 1]
elif superhost_filter == "Regular Only":
    filtered_df = filtered_df[filtered_df['host_is_superhost'] == 0]

if day_filter == "Weekend Only":
    filtered_df = filtered_df[filtered_df['is_weekend'] == 1]
elif day_filter == "Weekday Only":
    filtered_df = filtered_df[filtered_df['is_weekend'] == 0]

# Use filtered_df for all displays
df = filtered_df

# ==================== 6. HEADER & KPIs ====================
st.markdown(f"""
<div class="header-container">
    <h1>Airbnb Analytics Dashboard</h1>
    <p style="font-size: 16px; margin-top: 10px; opacity: 0.9;">Showing {len(df):,} of {len(load_data()):,} listings (outliers removed using IQR method)</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{len(df):,}</div><div class="kpi-label">Listings</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">${df["realSum"].mean():.0f}</div><div class="kpi-label">Avg Price</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{df["guest_satisfaction_overall"].mean():.1f}</div><div class="kpi-label">Rating</div></div>', unsafe_allow_html=True)

# ==================== 7. MAP SECTION ====================
st.markdown("---")
st.markdown("### Geographic Intelligence")

with st.container():
    map_df = df.sample(1500, random_state=42)

    fig_map = px.scatter_mapbox(
        map_df,
        lat="latitude",
        lon="longitude",
        color="realSum",
        color_continuous_scale=["#FF69B4", "#FF1493", "#C71585"],
        size_max=25,
        zoom=4,
        height=600,
        hover_name="city",
    )

    fig_map.update_layout(
        mapbox_style="carto-positron",
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False
    )
    fig_map.update_traces(marker=dict(size=20, opacity=1.0))

    st.plotly_chart(fig_map, use_container_width=True, on_select="rerun")

    # Prediction
    selected = st.session_state.get("plotly_selected")
    if selected and len(selected["points"]) > 0:
        idx = selected["points"][0]["pointIndex"]
        row = map_df.iloc[idx]
        
        model = load_model()
        if model:
            with st.spinner("Analyzing..."):
                time.sleep(0.3)
                test_row = df.drop(columns=["realSum"]).iloc[0:1].copy()
                test_row["city"] = row["city"]
                test_row["room_type"] = row["room_type"]
                test_row["person_capacity"] = 2
                test_row["cleanliness_rating"] = 9
                test_row["dist"] = row["dist"]
                test_row["is_weekend"] = 0
                pred_price = np.expm1(model.predict(test_row)[0])

            st.markdown(f"""
            <div class="prediction-result" style="margin: 20px auto; max-width: 600px;">
                <h3>{row['city'].capitalize()} • {row['room_type']}</h3>
                <h1 style="font-size: 50px; margin: 10px 0;">${pred_price:.0f}</h1>
                <p>Predicted Nightly Rate</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("### Market Breakdown")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Satisfaction Score")
    avg_satisfaction = df['guest_satisfaction_overall'].mean()
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = avg_satisfaction,
        domain = {'x': [0, 1], 'y': [0, 1]},
        number = {'font': {'size': 35, 'color': AIRBNB_COLOR}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': '#000000', 'tickfont': {'color': '#000000'}},
            'bar': {'color': AIRBNB_COLOR},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': border_color,
            'steps': [
                {'range': [0, 50], 'color': "#FFCDD2"},
                {'range': [50, 80], 'color': "#EF9A9A"},
                {'range': [80, 100], 'color': "rgba(255, 56, 92, 0.2)"}
            ],
        }
    ))
    fig_gauge.update_layout(
        template=plotly_template, 
        height=300, 
        margin=dict(l=10,r=10,t=30,b=10), 
        paper_bgcolor=chart_bg, 
        plot_bgcolor=chart_bg,
        font=dict(color='#000000')
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with col2:
    st.markdown("#### Room Types")
    room_counts = df['room_type'].value_counts().reset_index()
    room_counts.columns = ['room_type', 'count']
    fig_pie = px.pie(room_counts, values='count', names='room_type', hole=0.45, color_discrete_sequence=[AIRBNB_COLOR, "#FF8A80", "#FFCDD2"])
    fig_pie.update_traces(textinfo='percent', textfont=dict(size=14, color='white'), marker=dict(line=dict(color=card_bg, width=3)))
    fig_pie.update_layout(
        template=plotly_template, 
        height=300, 
        margin=dict(l=10,r=10,t=30,b=10), 
        paper_bgcolor=chart_bg,
        plot_bgcolor=chart_bg,
        font=dict(color='#000000'), 
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center", font=dict(color='#000000'))
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col3:
    st.markdown("#### Price Range")
    fig_box = px.box(df, x="room_type", y="realSum", color="room_type", color_discrete_sequence=[AIRBNB_COLOR, "#FF5A5F", "#FF8A80"])
    fig_box.update_layout(
        template=plotly_template, 
        height=300, 
        margin=dict(l=10,r=10,t=30,b=10), 
        paper_bgcolor=chart_bg,
        plot_bgcolor=chart_bg,
        font=dict(color='#000000'), 
        showlegend=False, 
        yaxis=dict(title="Price ($)", range=[0, 500], gridcolor=chart_grid_color, title_font=dict(color='#000000'), tickfont=dict(color='#000000')), 
        xaxis=dict(title=None, showticklabels=True, tickfont=dict(color='#000000'))
    )
    st.plotly_chart(fig_box, use_container_width=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("#### Weekend vs Weekday")
    weekend_data = df.groupby('is_weekend')['realSum'].mean().reset_index()
    weekend_data['Day Type'] = weekend_data['is_weekend'].map({0: 'Weekday', 1: 'Weekend'})
    fig_bar_week = px.bar(weekend_data, x='Day Type', y='realSum', color='Day Type', color_discrete_map={'Weekday': "#FF8A80", 'Weekend': AIRBNB_COLOR})
    fig_bar_week.update_traces(text=None)
    fig_bar_week.update_layout(
        template=plotly_template, 
        height=300, 
        margin=dict(l=10,r=10,t=30,b=10), 
        paper_bgcolor=chart_bg,
        plot_bgcolor=chart_bg,
        font=dict(color='#000000'), 
        showlegend=False, 
        yaxis=dict(title="Avg Price ($)", showgrid=True, gridcolor=chart_grid_color, title_font=dict(color='#000000'), tickfont=dict(color='#000000')), 
        xaxis=dict(title=None, tickfont=dict(color='#000000'))
    )
    st.plotly_chart(fig_bar_week, use_container_width=True)

with col5:
    st.markdown("#### Superhost Status")
    sh_counts = df['host_is_superhost'].value_counts().reset_index()
    sh_counts.columns = ['Status', 'Count']
    sh_counts['Label'] = sh_counts['Status'].map({0: 'Regular', 1: 'Superhost'})
    fig_sh = px.pie(sh_counts, values='Count', names='Label', hole=0.6, color='Label', color_discrete_map={'Superhost': AIRBNB_COLOR, 'Regular': "#FFCDD2"})
    fig_sh.update_traces(textinfo='percent', textfont=dict(size=14, color='white'), marker=dict(line=dict(color=card_bg, width=3)))
    fig_sh.update_layout(
        template=plotly_template, 
        height=300, 
        margin=dict(l=10,r=10,t=30,b=10), 
        paper_bgcolor=chart_bg,
        plot_bgcolor=chart_bg,
        font=dict(color='#000000'), 
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center", font=dict(color='#000000'))
    )
    st.plotly_chart(fig_sh, use_container_width=True)

with col6:
    st.markdown("#### Price by Capacity")
    cap_data = df.groupby('person_capacity')['realSum'].mean().reset_index()
    fig_cap = px.bar(cap_data, x='person_capacity', y='realSum')
    fig_cap.update_traces(marker_color=AIRBNB_COLOR)
    fig_cap.update_traces(text=None)
    fig_cap.update_layout(
        template=plotly_template, 
        height=300, 
        margin=dict(l=10,r=10,t=30,b=10), 
        paper_bgcolor=chart_bg,
        plot_bgcolor=chart_bg,
        font=dict(color='#000000'), 
        yaxis=dict(title="Avg Price ($)", showgrid=True, gridcolor=chart_grid_color, title_font=dict(color='#000000'), tickfont=dict(color='#000000')), 
        xaxis=dict(title="Guests", title_font=dict(color='#000000'), tickfont=dict(color='#000000'))
    )
    st.plotly_chart(fig_cap, use_container_width=True)

st.markdown("---")

st.markdown("### AI Smart Predictor")
st.markdown("Customize your listing details below to get an instant price estimation.")

with st.container():
    with st.form("ai_price_form"):
        c_in1, c_in2, c_in3 = st.columns(3)
        with c_in1:
            input_city = st.selectbox("Choose City", df['city'].unique())
            input_room = st.selectbox("Room Type", df['room_type'].unique())
        with c_in2:
            input_capacity = st.number_input("Guests Capacity", min_value=1, max_value=6, value=2)
            input_cleanliness = st.slider("Cleanliness Rating (1-10)", 1, 10, 9)
        with c_in3:
            input_dist = st.slider("Distance from Center (km)", 0.0, 10.0, 2.0)
            st.write("")
            st.write("**Weekend Day**")
            input_weekend = st.checkbox("Check if weekend", value=False, label_visibility="collapsed")
            
        submit_btn = st.form_submit_button("Calculate Predicted Price", use_container_width=True)

    if submit_btn:
        model = load_model()
        if model:
            with st.spinner("Processing with AI..."):
                time.sleep(0.5)
                base_row = df[df['city'] == input_city].iloc[0].copy()
                base_row["room_type"] = input_room
                base_row["person_capacity"] = input_capacity
                base_row["cleanliness_rating"] = input_cleanliness
                base_row["dist"] = input_dist
                base_row["is_weekend"] = 1 if input_weekend else 0
                
                if "realSum" in base_row:
                    input_df = pd.DataFrame([base_row]).drop(columns=["realSum"])
                else:
                    input_df = pd.DataFrame([base_row])
                
                try:
                    predicted_log = model.predict(input_df)[0]
                    predicted_price = np.expm1(predicted_log)
                    st.markdown(f"""
                    <div class="prediction-result" style="margin: 20px auto; max-width: 600px;">
                        <p style="font-size:18px; opacity:0.9;">Estimated Price for <b>{input_city.capitalize()}</b></p>
                        <h1 style="font-size: 60px; margin: 10px 0; font-weight:800;">${predicted_price:.2f}</h1>
                        <p style="opacity:0.8;">{input_room} • {input_capacity} Guests • {input_dist}km from center</p>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Prediction Error: {e}")
        else:
            st.error("Model not loaded. Please check file path.")