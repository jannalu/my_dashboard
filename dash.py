import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

# SET CONFIG 
st.set_page_config(
    layout="wide",
    page_title="Blue Nile Jewelry Store Customer Dashboard", 
    page_icon=":diamond_shape_with_a_dot_inside:"
)

geolocator = Nominatim(user_agent="store_locator", timeout=10)

# FUNCTIONS
@st.cache_data
def load_data(file):
    days_order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    
    df = pd.read_csv(file, sep="\t")
    df["Time of Day"] = pd.to_datetime(df["Time of Day"])
    df['Hour'] = df["Time of Day"].dt.hour
    df['Minute'] = df["Time of Day"].dt.minute

    # Ensure Day of Week is ordered
    df['Day of Week'] = pd.Categorical(df['Day of Week'], categories=days_order, ordered=True)
    return df

def sidebar_filters(df):
    st.sidebar.markdown("<h2 style='font-size: 22px; padding-left:10px'>⚙️ Filters</h2>", unsafe_allow_html=True)

    polygon_ids = df['Polygon ID'].unique().tolist()
    alias_to_id = {}
    for pid in polygon_ids:
        location_text = pid.split('|')[0]
        if '-' in location_text:
            location = location_text.split('-')[1]
        else:
            location = location_text.split('Nile')[1]
        alias_to_id[location.strip()] = pid

    display_names = list(alias_to_id.keys())

    selected_aliases = st.sidebar.multiselect(
        'Select store locations:', 
        display_names,
        default=display_names[:2]
    )

    selected_ids = [alias_to_id[alias] for alias in selected_aliases]
    filtered_df = df[df['Polygon ID'].isin(selected_ids)]

    return filtered_df, selected_ids, alias_to_id

def clean_store_name(pid):
    location_text = pid.split('|')[0]
    if '-' in location_text:
        location = location_text.split('-')[1]
    else:
        location = location_text.split('Nile')[1]
    return location.strip()

# ------------------- PLOTTING FUNCTIONS -------------------

def plot_visits_per_day(df, selected_ids):
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    st.subheader("Breakdown of Visits per Day of Week")

    df = df[df["Polygon ID"].isin(selected_ids)]
    df['Store'] = df['Polygon ID'].apply(clean_store_name)

    visits_per_day = (
        df.groupby(['Store', 'Day of Week'])
        .size()
        .reset_index(name='Visit Count')
    )

    visits_per_day['Day of Week'] = pd.Categorical(
        visits_per_day['Day of Week'],
        categories=days,
        ordered=True
    )

    fig = px.bar(
        visits_per_day,
        x='Day of Week',
        y='Visit Count',
        color='Store',
        barmode='group',
        title="Visits per Day of Week by Store"
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_visits_per_hour_by_day(df, selected_ids, selected_day):
    st.subheader(f"Visits per Hour on {selected_day}")

    df = df[df["Polygon ID"].isin(selected_ids)]
    df['Store'] = df['Polygon ID'].apply(clean_store_name)

    filtered = df[df['Day of Week'] == selected_day]
    hour_counts = (
        filtered.groupby(['Store', 'Hour'])
        .size()
        .reset_index(name='Visit Count')
    )

    fig = px.bar(
        hour_counts,
        x='Hour',
        y='Visit Count',
        color='Store',
        barmode='group'
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_visits_per_min(df, selected_ids, selected_day):
    st.subheader("Breakdown of Visits per Minute")
    
    hour = st.sidebar.slider("Select an hour of the day: ", 0, 23, 12)

    df = df[df["Polygon ID"].isin(selected_ids)]
    df['Store'] = df['Polygon ID'].apply(clean_store_name)

    df_day_hour = df[(df['Day of Week'] == selected_day) & (df['Hour'] == hour)]

    minute_counts = (
        df_day_hour.groupby(['Store', 'Minute'])
        .size()
        .reset_index(name='Visit Count')
    )

    all_minutes = pd.DataFrame({'Minute': range(60)})
    expanded = []
    for store in df['Store'].unique():
        tmp = all_minutes.copy()
        tmp['Store'] = store
        expanded.append(tmp)
    all_minutes_df = pd.concat(expanded, ignore_index=True)

    minute_counts = pd.merge(
        all_minutes_df,
        minute_counts,
        on=['Store', 'Minute'],
        how='left'
    ).fillna({'Visit Count': 0})

    fig = px.bar(
        minute_counts,
        x='Minute',
        y='Visit Count',
        color='Store',
        barmode='group',
        title=f'Visits per Minute on {selected_day} between {hour}:00 and {hour+1}:00'
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_yearly_visits_by_store(df, selected_ids):
    st.subheader("📆 Yearly Visit Trends by Store (2022)")

    df = df[df['Polygon ID'].isin(selected_ids)]
    df['Store'] = df['Polygon ID'].apply(clean_store_name)
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')
    df['Month_Num'] = df['Date'].dt.month
    df['Month'] = df['Date'].dt.month_name()

    visits_by_month_store = (
        df.groupby(['Month_Num', 'Month', 'Store'])
        .size()
        .reset_index(name='Visit Count')
        .sort_values('Month_Num')
    )

    fig = px.line(
        visits_by_month_store,
        x='Month',
        y='Visit Count',
        color='Store',
        markers=True,
        title='Monthly Visits by Store'
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------- MAP FUNCTIONS -------------------
def map_locations():
    long_lat_list = [
        (45.45028430922948, -122.78192245936043),
        (30.403526657405834, -97.72236904839427),
        (29.739593752839355, -95.46403769074766),
        (38.77383623216167, -121.26905021921182),
        (42.76677289198521, -71.23140510552382),
        (33.50427846620759, -111.92909888875768),
        (40.9178842743316, -74.076354432604)
    ]

    store_names = [
        "Washington Square, Portland OR",
        "Austin, TX",
        "Houston, TX",
        "Roseville, CA",
        "Salem, NH",
        "Scottsdale, AZ",
        "Paramus, NJ"
    ]

    m = folium.Map(location=[39.5, -98.35], zoom_start=3, tiles='OpenStreetMap')
    for (lat, lon), name in zip(long_lat_list, store_names):
        folium.Marker(location=[lat, lon], popup=name, tooltip=name).add_to(m)

    st.subheader("Store Locations")
    st_folium(m, width=500, height=400)

def show_map(df, selected_ids):
    st.subheader("Customer Distribution Sample")
    st.write(
        "Mapped distribution of customer origins based on evening location data "
        "for the selected store location(s)."
    )

    # Store location coordinates
    long_lat_list = {
        "Blue Nile Washington Square, Portland, OR|9695391": (45.45028430922948, -122.78192245936043),
        "Blue Nile Blue Nile Jewelry - Domain Northside, Austin, TX|11050622": (30.403526657405834, -97.72236904839427),
        "Blue Nile Blue Nile Jewelry - Houston Galleria, Houston, TX|11050619": (29.739593752839355, -95.46403769074766),
        "Blue Nile Blue Nile Jewelry - Roseville Galleria1151 Galleria Blvd, Suite 120,,Roseville,95678,CA,USA, Roseville, CA|11259307": (38.77383623216167, -121.26905021921182),
        "Blue Nile The Mall at Rockingham Park, Salem, NH|9695393": (42.76677289198521, -71.23140510552382),
        "Blue Nile Blue Nile Jewelry - Fashion Square, Scottsdale, AZ|11088822": (33.50427846620759, -111.92909888875768),
        "Blue Nile Blue Nile Jewelry - Garden State Plaza, Paramus, NJ|11050629": (40.9178842743316, -74.076354432604)
    }

    # Filter only selected stores
    filtered_df = df[df["Polygon Id"].isin(selected_ids)]
    df["Polygon Short"] = df["Polygon Id"].str.split("|").str[0]

    # Scatter plot of customer distribution
    fig = px.scatter_mapbox(
        filtered_df,
        lat="Common Evening Lat",
        lon="Common Evening Long",
        color="Polygon Id",
        zoom=3,
        width=800,
        height=500
    )

    # Add store markers
    for store_id in selected_ids:
        matched_id = next((key for key in long_lat_list if key.strip() == store_id.strip()), None)
        if matched_id:
            lat, lon = long_lat_list[matched_id]
            fig.add_trace(go.Scattermapbox(
                lat=[lat],
                lon=[lon],
                mode="markers+text",
                marker=dict(size=14, color="red"),
                text=["Store Location"],
                textposition="top right",
                name=matched_id.split("|")[0]
            ))

    # Center map on first store selected
    if selected_ids:
        first_id = selected_ids[0]
        lat, lon = long_lat_list.get(first_id, (37.0902, -95.7129))  # Default to USA center if missing
        fig.update_layout(mapbox_center={"lat": lat, "lon": lon}, mapbox_zoom=4)

    fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0, "t":0, "l":0, "b":0},
            legend=dict(
                font=dict(size=10),
                orientation="h",       # horizontal legend
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                itemsizing='constant'
            )
        )

    st.plotly_chart(fig, use_container_width=True)

# ------------------- MAIN -------------------
st.markdown("<h1 style='text-align: center;'> 💎 Blue Nile Jewelry Customer Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px'>Analyze customer locations and visits at different days and times for 7 different Blue Nile Jewelry stores across the U.S.<br>Use the sidebar to select one or more store locations.</p>", unsafe_allow_html=True)

df = load_data("week2/week2-ds.tsv")
df_week3 = pd.read_csv("week3/week3-ds-cel.tsv", sep="\t")

col1, col2 = st.columns(2)
filtered_df, ids, alias_map = sidebar_filters(df)

days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
selected_day = st.sidebar.selectbox("Select a day:", days, index=0)

if not ids:
    st.warning("⚠️ Please select at least one store location from the sidebar to see the dashboard.")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        map_locations()
    with col2:
        show_map(df_week3, ids)

    plot_visits_per_day(filtered_df, ids)
    plot_visits_per_hour_by_day(filtered_df, ids, selected_day)
    plot_visits_per_min(filtered_df, ids, selected_day)
    plot_yearly_visits_by_store(df, ids)