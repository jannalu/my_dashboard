import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import time, folium
from streamlit_folium import st_folium
import plotly.graph_objects as go


## bar chart of the amount of visits every minute for every hour
## do this for each stores

## scatter plot of where people live for each store
## bar chart of days of week

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
    df = pd.read_csv(file, sep="\t")
    df["Time of Day"] = pd.to_datetime(df["Time of Day"])
    df['Hour'] = df["Time of Day"].dt.hour
    df['Minute'] = df["Time of Day"].dt.minute
    return df

def get_loc(df):
    # parse to get city and zipcode
    locations = df['Polygon ID'].dropna().unique()
    locations_df = pd.DataFrame(locations, columns=['store_string'])
    parsed_loc = locations_df['store_string']

    return parsed_loc


def geocode_loc(df):
    locations_list = ['Blue Nile, Scottsdale, AZ',
                      'Blue Nile, Austin, TX',
                      'Blue Nile, Houston, TX',
                      'Blue Nile, Salem, NH',
                      'Blue Nile, Paramus, NJ',
                      'Blue Nile, Portland, OR',
                      'Blue Nile, Roseville, CA']

    geoloc_list = []
    for loc in locations_list:
        print(loc)
        location = geolocator.geocode(loc)
        if location: 
            geoloc_list.append({'location': loc, 'lat': location.latitude, 'lon': location.longitude})

        else:
            geoloc_list.append({'location': loc, 'lat': None, 'lon': None})
            print(location)


        time.sleep(1)

    geo_df = pd.DataFrame(geoloc_list)
    geo_df['clean_location'] = geo_df['location']

    return geo_df

# Store Locations Map
def map_locations():
    long_lat_list = [(45.45028430922948, -122.78192245936043), ## washington square, portland or
                     (30.403526657405834, -97.72236904839427), ## austin tx
                     (29.739593752839355, -95.46403769074766), ## houston tx
                     (38.77383623216167, -121.26905021921182), ## roseville ca
                     (42.76677289198521, -71.23140510552382), ## salem nh
                     (33.50427846620759, -111.92909888875768), ## scottsdale az
                     (40.9178842743316, -74.076354432604) ## paramus nj
    ]

    store_names = ["Washington Square, Portland OR",
                "Austin, TX",
                "Houston, TX",
                "Roseville, CA",
                "Salem, NH",
                "Scottsdale, AZ",
                "Paramus, NJ"
    ]

    # Create base map centered around the U.S.
    m = folium.Map(location=[39.5, -98.35], zoom_start=3, tiles='OpenStreetMap')

    # Add markers
    for (lat, lon), name in zip(long_lat_list, store_names):
        folium.Marker(location=[lat, lon], popup=name, tooltip=name).add_to(m)

    # Render map in Streamlit
    st.subheader("Store Locations")
    st_folium(m, width=500, height=400)

# Sidebar
def sidebar_filters(df):
    st.sidebar.markdown("<h2 style='font-size: 22px; padding-left:10px'>⚙️ Filters</h2>", unsafe_allow_html=True)

    polygon_ids = df['Polygon ID'].unique().tolist()

    alias_to_id = {}

    for pid in polygon_ids:
        location_text = pid.split('|')[0]
        if '-' in location_text:
            location= location_text.split('-')[1]
        else:
            location= location_text.split('Nile')[1]
        
        alias_to_id[location] = pid
    
    display_names = list(alias_to_id.keys())
    selected_alias = st.sidebar.selectbox('Select a store location:', display_names)
    selected_id = alias_to_id[selected_alias]

    df = df[df['Polygon ID'] == selected_id]

    return df, selected_id

def plot_visits_per_min(df, selected_id):
    st.subheader("Breakdown of Visits per Minute")
    st.write("Use the sidebar to select an hour of the day.")


    hour = st.sidebar.slider("Select an hour of the day: ", 0, 23, 12)
    df_hour = df[df['Hour'] == hour]

    minute_counts = df_hour['Minute'].value_counts().sort_index().reset_index()
    minute_counts.columns = ['Minute', 'Visit Count']
    minute_counts['Minute'] = minute_counts['Minute'].apply(lambda x: f'{x:02}')


    most_visited_minute = minute_counts.loc[minute_counts['Visit Count'].idxmax(), 'Minute']


    fig = px.bar(
        minute_counts,
        x='Minute',
        y='Visit Count',
        title=f'Number of Visits per Minute Between {hour}:00 and {hour+1}:00',
        color_discrete_sequence=['gray'],
        opacity=0.7
    )

    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=2, showgrid=True),
        yaxis=dict(title='Number of Visits', showgrid=True),
        plot_bgcolor='white',
        bargap=0
    )

    st.plotly_chart(fig, use_container_width=True)
    return most_visited_minute

def plot_visits_per_day(df, selected_id):
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    st.subheader("Breakdown of Visits per Day of Week")
    df = df[df["Polygon ID"] == selected_id]

    visits_per_day = df['Day of Week'].value_counts().reindex(days).reset_index()
    visits_per_day.columns = ['Day of Week', 'Visit Count']

    most_visited_day = visits_per_day.loc[visits_per_day['Visit Count'].idxmax(), 'Day of Week']

    selected_id = selected_id.split('|')[0]
    if '-' in selected_id:
        location= selected_id.split('-')[1]
    else:
        location= selected_id.split('Nile')[1]

    fig = px.bar(
        visits_per_day,
        x='Day of Week',
        y='Visit Count',
        title=f"Visits per Day at Blue Nile at {location}",
        labels={'Day of Week': 'Day', 'Visit Count': 'Number of Visits'},
        color_discrete_sequence=['lightblue'],
        opacity=0.8
    )

    fig.update_layout(bargap=0, 
                      xaxis_title="Day of the Week", 
                      yaxis_title="Number of Visits")
    
    st.plotly_chart(fig, use_container_width=True)

    return most_visited_day

def plot_visits_per_hour_by_day(df, selected_id):
    st.subheader("Breakdown of Visits per Hour")
    st.write("Use the sidebar to select a day of the week.")

    df = df[df["Polygon ID"] == selected_id]

    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    selected_day = st.sidebar.selectbox("Select a day:", days, index =0)
    df_day = df[df["Day of Week"] == selected_day]

    visits_per_hour = df_day['Hour'].value_counts().sort_index().reset_index()
    visits_per_hour.columns = ['Hour', 'Visit Count']

    all_hours = pd.DataFrame({'Hour': list(range(24))})
    visits_per_hour = all_hours.merge(visits_per_hour, on='Hour', how='left').fillna(0)

    visits_per_hour['Visit Count'] = visits_per_hour['Visit Count'].astype(int)
    most_visited_hour = visits_per_hour.loc[visits_per_hour['Visit Count'].idxmax(), 'Hour']


    fig = px.bar(
        visits_per_hour,
        x='Hour',
        y='Visit Count',
        title=f'Visits per hour on {selected_day}',
        labels={'Hour': 'Hour of Day', 'Visit Count': 'Number of Visits'},
        color_discrete_sequence=['teal'],
        width=600,
        opacity=0.8
    )

    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title='Number of Visits'),
        plot_bgcolor='white',
        bargap=0.1
    )
    st.plotly_chart(fig, use_container_width=False)
    return selected_day, most_visited_hour


def display_summary(day, hour, min, selected_day, id):

    id = id.split('|')[0]
    if '-' in id:
        id= id.split('-')[1]
    else:
        id= id.split('Nile')[1]

    st.subheader(f"Summary statistics for {id}")
    st.write(f"**⏰ Busiest day of the week:** {day}")
    st.write(f"**⏰ Busiest time on {selected_day}:** {hour}:{min}")

def plot_yearly_visits_by_store(df):
    st.subheader("📆 Yearly Visit Trends by Store (2022)")

    # Convert date and extract month number
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')
    df['Month_Num'] = df['Date'].dt.month
    df['Month_Name'] = df['Date'].dt.month_name()

    # Group by month number to maintain correct order
    visits_by_month_store = (
        df.groupby(['Month_Num', 'Polygon ID'])
        .size()
        .reset_index(name='Visit Count')
    )

    # Add month name for display
    visits_by_month_store['Month'] = visits_by_month_store['Month_Num'].apply(lambda x: pd.to_datetime(str(x), format='%m').strftime('%B'))

    # Sort by month number to ensure correct order in the plot
    visits_by_month_store = visits_by_month_store.sort_values('Month_Num')

    # Plot
    fig = px.line(
        visits_by_month_store,
        x='Month',
        y='Visit Count',
        color='Polygon ID',
        markers=True,
        title='Monthly Visits by Store'
    )

   
    st.write("""
    **Double click** on a store in the legend to isolate it or **single click** to remove it.
    """)

    fig.update_layout(
        width=1000,
        height=700,
        xaxis_title='Month',
        yaxis_title='Number of Visits',
        plot_bgcolor='white',
        legend=dict(
            orientation="v",         
            yanchor="top",           
            y= -0.3,                  
            xanchor="center",
            x=0.5,
            font=dict(size=15)
        )
    )

    st.plotly_chart(fig, use_container_width=True)


# Customer distribution sample map
def show_map(df, id):
    st.subheader("Customer Distribution Sample")
    st.write("Mapped distribution of customer origins based on evening location data for the selected store location.")
    df = df[df["Polygon Id"] == id]

    long_lat_list = {
        "Blue Nile Washington Square, Portland, OR|9695391": (45.45028430922948, -122.78192245936043), ## washington square, portland or
        "Blue Nile Blue Nile Jewelry - Domain Northside, Austin, TX|11050622":(30.403526657405834, -97.72236904839427), ## austin tx
        "Blue Nile Blue Nile Jewelry - Houston Galleria, Houston, TX|11050619":(29.739593752839355, -95.46403769074766), ## houston tx
        "Blue Nile Blue Nile Jewelry - Roseville Galleria1151 Galleria Blvd, Suite 120,,Roseville,95678,CA,USA, Roseville, CA|11259307":(38.77383623216167, -121.26905021921182), ## roseville ca
        "Blue Nile The Mall at Rockingham Park, Salem, NH|9695393":(42.76677289198521, -71.23140510552382), ## salem nh
        "Blue Nile Blue Nile Jewelry - Fashion Square, Scottsdale, AZ|11088822":(33.50427846620759, -111.92909888875768), ## scottsdale az
        "Blue Nile Blue Nile Jewelry - Garden State Plaza, Paramus, NJ|11050629":(40.9178842743316, -74.076354432604) ## paramus nj
    }

    matched_id = next((key for key in long_lat_list if key.strip() == id.strip()), None)

    fig = px.scatter_mapbox(
        df,
        lat="Common Evening Lat",
        lon="Common Evening Long",
        zoom=5,
        width=500, 
        height=400,
    )

    if matched_id:
        lat, lon = long_lat_list[matched_id]
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode="markers+text",
            marker=dict(size=14, color="red"),
            # text=["Store Location"],
            textposition="top right",
            name="Store Location"
        ))

    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(mapbox_center={"lat": lat, "lon": lon}, mapbox_zoom=10)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(dragmode="zoom")  
    st.plotly_chart(fig, use_container_width=True)

# MAIN
st.markdown("<h1 style='text-align: center;'> 💎Blue Nile Jewelry Customer Dashboard</h1>", unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 18px'>Analyze customer locations and " \
"visits at different days and times for 7 different Blue Nile Jewelry stores across " \
"the U.S. <br>Use the sidebar to select a store location.</p>", unsafe_allow_html=True)


df = load_data("week2/week2-ds.tsv")
df_week3 = pd.read_csv("week3/week3-ds-cel.tsv", sep="\t")
# st.write(df_week3.head()) 

col1, col2 = st.columns(2)
filtered_df, id = sidebar_filters(df)

with col1:
    map_locations()

with col2:
    show_map(df_week3, id)


col3, col4 = st.columns(2)

with col3:
    busy_day = plot_visits_per_day(filtered_df, id)

with col4:
    day, busy_hour = plot_visits_per_hour_by_day(filtered_df, id)

busy_min = plot_visits_per_min(filtered_df, id)

display_summary(busy_day, busy_hour, busy_min, day, id)
plot_yearly_visits_by_store(df)
