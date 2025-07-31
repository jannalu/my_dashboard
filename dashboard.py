import streamlit as st
import pandas as pd

## bar chart of the amount of visits every minute for every hour
## do this for each store


st.set_page_config(layout="wide", page_title="Blue Nile Jewelry", page_icon=":diamond_shape_with_a_dot_inside:")

st.title("Blue Nile Jewelry Data")
st.write(
    """
    ##
    Examining Blue Nile Jewelry's customer visits across its 7 different store locations. 
    Use the sidebar to filter the data based on data source and/or time zone.
    """

    )
df = pd.read_csv("week2/week2-ds.tsv", sep="\t")

data_source_options = df['Data Source'].unique().tolist()

data_source = st.sidebar.multiselect(
    'Choose a data source to fiter by: ', data_source_options
    )


if data_source:
    df = df[df['Data Source'].isin(data_source)]

# time_zone = st.sidebar.selectbox(
#     'Choose a time zone to filter by: ',
#     ('All', 'America/Phoenix', 'America/Chicago', 'America/Los_Angeles', 'America/New_York')
# )

# if (time_zone != 'All'):  
#     df = df[df['Time Zone'] == time_zone]
# else:
#     df = df

time_zone_options = df['Time Zone'].unique().tolist()

time_zone = st.sidebar.multiselect(
    'Choose a time zone to filter by: ', time_zone_options
    )

if time_zone:   
    df = df[df['Time Zone'].isin(time_zone)]

add_slider = st.sidebar.slider(
    'Select a range of values',
    0.0, 100.0, (25.0, 75.0)
)

st.write(df)
