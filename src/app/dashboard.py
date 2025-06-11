import streamlit as st
import plotly.express as px
from streamlit_folium import folium_static
import folium
import pandas as pd
import numpy as np
import random
import streamlit_option_menu
from streamlit_option_menu import option_menu
from plotly.subplots import make_subplots
#from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import plotly.graph_objs as go 


# Database Connection Details

POSTGRES_CONNECTION = {
    "dialect": "postgresql",
    "host": "postgres",
    "port": "5432",
    "username": "myuser",
    "password": "mypassword",
    "database": "mydatabase"
}

# Fetch data function

def fetch_data(sql, params=None):
    conn = st.connection("postgres", type="sql", **POSTGRES_CONNECTION)
    try:
        if params:
            data = conn.query(sql, params)
        else:
            data = conn.query(sql)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()


# Sidebar for navigation
    
def setup_sidebar():
    with st.sidebar:
        selected = option_menu(
            menu_title="MENU",
            options=["Home", "Measures", "Hospitals", "Budget", "Contact us"],
            icons=["house", "bar-chart", "hospital", "activity", "envelope"],
            menu_icon="cast",
            default_index=0,
        )
    return selected


# Home Page

def display_home_page():
    st.title("Welcome to Australian Healthcare Resource Allocation App")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write("")
    with col2:
        st.image("/app/data/images/logo.png", use_column_width=True)  
    with col3:
        st.write("")

    st.write("""
        This application is designed to facilitate healthcare resource allocation through data-driven insights. 
        Navigate through the various sections using the sidebar to explore different metrics and tools available to you.
    """)

    st.markdown("### Overview")
    st.write("""
        Efficient allocation of healthcare resources is critical to improving patient outcomes and optimizing costs. 
        This application provides a comprehensive suite of tools for analyzing healthcare data, forecasting trends, 
        and making informed decisions about resource distribution.
    """)

    st.markdown("### Getting Started")
    st.write("""
        - **Step 1:** Use the sidebar to select a section (e.g., Measures, Hospitals, etc.).
        - **Step 2:** Choose the relevant options and filters to explore the data.
        - **Step 3:** View visualizations and insights to assist in decision-making.
    """)

    # Fetch the total number of datasets
    total_query = "SELECT COUNT(*) FROM datasets;"
    total_count_df = fetch_data(total_query)
    
    # Fetch the number of stored datasets
    stored_query = "SELECT COUNT(*) FROM datasets WHERE stored = TRUE;"
    stored_count_df = fetch_data(stored_query)
    
    # Extract the counts from the dataframes
    total_count = total_count_df.iloc[0, 0] if not total_count_df.empty else 0
    stored_count = stored_count_df.iloc[0, 0] if not stored_count_df.empty else 0
    
    # Calculate the percentage of stored datasets
    if total_count > 0:
        stored_percentage = stored_count / total_count
        stored_percentage_text = f"{stored_percentage * 100:.2f}%"
    else:
        stored_percentage = 0
        stored_percentage_text = "0.00%"


    st.markdown("### Data Storage Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Stored Datasets", value=stored_count)

    with col2:
        st.metric(label="Total Datasets", value=total_count)

    with col3:
        st.metric(label="Percentage Stored", value=stored_percentage_text)

    with st.expander('Learn More', expanded=True):
        st.write('''
            - **Data Sources:** 
              - [Australian Institute of Health and Welfare](https://www.aihw.gov.au)
              - [Australian Bureau of Statistics](https://www.abs.gov.au/statistics/people/population)
            - **Methodology:** The data is analyzed and presented in a way that supports healthcare administrators and policymakers 
              in making informed decisions about resource allocation.
        ''')

    # Optional: Add a button to navigate to the main dashboard
    if st.button("Go to Dashboard"):
        st.session_state['page'] = 'dashboard'




# Display Measures

def display_measures():
    st.title("Measures")
    st.markdown("### Explore Healthcare Metrics by State and Hospital")
    st.markdown("""
    This section of the dashboard allows you to explore detailed metrics for various healthcare measures across different states in Australia.""")
    
    sql_query_codes = '''
    SELECT
        ds.*,
        m.measurename,
        rm.reportedmeasurename
    FROM
        datasets ds
    LEFT JOIN
        measurements m ON ds.measurecode = m.measurecode
    LEFT JOIN
        reported_measurements rm ON ds.reportedmeasurecode = rm.reportedmeasurecode
    WHERE
        ds.stored = TRUE;
    '''

    df_measures = fetch_data(sql_query_codes)
    selected_measure = st.selectbox("Select Measure", np.sort(df_measures['measurename'].unique()))
    df_reported_measures = df_measures[df_measures['measurename'] == selected_measure]
    selected_reported_measure = st.selectbox("Select Reported Measure", np.sort(df_reported_measures['reportedmeasurename'].unique()))

    # Fetch the list of states
    sql_query_states = '''
    SELECT DISTINCT
        state
    FROM
        hospitals
    WHERE
        open_closed = 'Open';
    '''
    df_states = fetch_data(sql_query_states)
    state_list = df_states['state'].unique()

    selected_state = st.selectbox("Select State", np.sort(state_list))

    safe_measure = selected_measure.replace("'", "''")  # rudimentary SQL injection protection
    safe_reported_measure = selected_reported_measure.replace("'", "''")  # rudimentary SQL injection protection
    safe_state = selected_state.replace("'", "''")  # rudimentary SQL injection protection

    sql_query_state = f'''
    SELECT
        info.value,
        ds.reportingstartdate,
        info.reportingunitcode,
        h.name as hospital_name,
        h.latitude,
        h.longitude
    FROM
        datasets ds
    JOIN
        measurements m ON ds.measurecode = m.measurecode
    JOIN
        reported_measurements rm ON ds.reportedmeasurecode = rm.reportedmeasurecode
    JOIN
        info ON ds.datasetid = info.datasetid
    JOIN
        hospitals h ON info.reportingunitcode = h.code
    WHERE
        m.measurename = '{safe_measure}' AND
        rm.reportedmeasurename = '{safe_reported_measure}' AND
        ds.stored = TRUE AND
        h.state = '{safe_state}'
    ORDER BY
        ds.reportingstartdate ASC;
    '''

    df_value = fetch_data(sql_query_state)

    if df_value.empty:
        st.write("No data found for the selected state. Displaying national data.")

        sql_query_national = f'''
        SELECT
            info.value,
            ds.reportingstartdate,
            info.reportingunitcode,
            h.name as hospital_name,
            h.latitude,
            h.longitude
        FROM
            datasets ds
        JOIN
            measurements m ON ds.measurecode = m.measurecode
        JOIN
            reported_measurements rm ON ds.reportedmeasurecode = rm.reportedmeasurecode
        JOIN
            info ON ds.datasetid = info.datasetid
        JOIN
            hospitals h ON info.reportingunitcode = h.code
        WHERE
            m.measurename = '{safe_measure}' AND
            rm.reportedmeasurename = '{safe_reported_measure}' AND
            ds.stored = TRUE AND
            info.reportingunitcode = 'NAT'
        ORDER BY
            ds.reportingstartdate ASC;
        '''

        df_value = fetch_data(sql_query_national)

    # Filter out NaN values
    df_value = df_value.dropna()

    if not df_value.empty:
        # Aggregate data by reporting date
        df_value_aggregated = df_value.groupby('reportingstartdate').agg({'value': 'mean'}).reset_index()

        # Time Series Plot
        st.markdown("### Time Series of Selected Measure")
        st.markdown("This plot shows the time series of the selected measure over time, along with the national average for comparison.")
        fig = px.line(df_value_aggregated, x='reportingstartdate', y='value', title=f'{selected_measure} - {selected_reported_measure} Over Time')

        # Fetch and plot national average
        sql_query_national_avg = f'''
        SELECT
            info.value,
            ds.reportingstartdate
        FROM
            datasets ds
        JOIN
            measurements m ON ds.measurecode = m.measurecode
        JOIN
            reported_measurements rm ON ds.reportedmeasurecode = rm.reportedmeasurecode
        JOIN
            info ON ds.datasetid = info.datasetid
        WHERE
            m.measurename = '{safe_measure}' AND
            rm.reportedmeasurename = '{safe_reported_measure}' AND
            ds.stored = TRUE AND
            info.reportingunitcode = 'NAT'
        ORDER BY
            ds.reportingstartdate ASC;
        '''
        df_national_avg = fetch_data(sql_query_national_avg)

        if not df_national_avg.empty:
            df_national_avg = df_national_avg.groupby('reportingstartdate').agg({'value': 'mean'}).reset_index()
            fig.add_trace(go.Scatter(x=df_national_avg['reportingstartdate'], y=df_national_avg['value'], mode='lines', name='National Average'))

        st.plotly_chart(fig)

        # Map of Hospitals
        st.markdown("### Hospital Locations")
        fig_map = px.scatter_mapbox(
            df_value, lat='latitude', lon='longitude', hover_name='hospital_name',
            hover_data={'latitude': False, 'longitude': False, 'value': True},
            title=f'Hospitals in {selected_state} Reporting {selected_measure}',
            mapbox_style="open-street-map", zoom=5,
            color_discrete_sequence=["darkblue"]
        )
        st.plotly_chart(fig_map)

        # Plot Selection
        st.markdown("### Choose Plots to Display")
        plot_options = st.multiselect(
            "Select the plots you want to see:",
            ["Time Series Decomposition", "Forecasting", "Distribution of Values", "Value Distribution by Hospital", "Heatmap of Values Over Time", "Ranking of Hospitals", "Correlation Analysis"]
        )

        # Time Series Decomposition
        if "Time Series Decomposition" in plot_options:
            st.markdown("### Time Series Decomposition")
            st.markdown("This section decomposes the time series into trend, seasonal, and residual components to analyze the underlying patterns in the data.")
            if len(df_value_aggregated) >= 24:  # Check if there are enough observations
                decomposition = seasonal_decompose(df_value_aggregated.set_index('reportingstartdate')['value'], model='additive', period=12)
                fig_trend = px.line(decomposition.trend.dropna(), title='Trend Component')
                fig_seasonal = px.line(decomposition.seasonal.dropna(), title='Seasonal Component')
                fig_residual = px.line(decomposition.resid.dropna(), title='Residual Component')
                st.plotly_chart(fig_trend)
                st.plotly_chart(fig_seasonal)
                st.plotly_chart(fig_residual)
            else:
                st.write("Not enough data for time series decomposition. At least 24 observations are required.")

        # Forecasting
        if "Forecasting" in plot_options:
            st.markdown("### Forecasting")
            st.markdown("This section provides a forecast of the selected measure for the upcoming months based on historical data.")
            forecast_horizon = st.slider("Select Forecast Horizon (Months)", 1, 24, 12, key="forecast_horizon")
            if len(df_value_aggregated) >= 12:
                model = ExponentialSmoothing(df_value_aggregated['value'], trend='add', seasonal=None).fit()
                forecast = model.forecast(forecast_horizon)
                fig_forecast = px.line(df_value_aggregated, x='reportingstartdate', y='value', title='Forecasting')
                fig_forecast.add_trace(go.Scatter(x=pd.date_range(df_value_aggregated['reportingstartdate'].iloc[-1], periods=forecast_horizon, freq='M'), y=forecast, mode='lines', name='Forecast'))
                st.plotly_chart(fig_forecast)
            else:
                st.write("Not enough data for forecasting. At least 12 observations are required.")

        # Histogram: Distribution of Values
        if "Distribution of Values" in plot_options:
            st.markdown("### Distribution of Values")
            st.markdown("This histogram shows the distribution of values for the selected measure across hospitals in the selected state.")
            fig_hist = px.histogram(df_value, x='value', nbins=20, title=f'Distribution of {selected_measure} - {selected_reported_measure}')
            st.plotly_chart(fig_hist)

        # Box Plot: Value Distribution by Hospital
        if "Value Distribution by Hospital" in plot_options:
            st.markdown("### Value Distribution by Hospital")
            st.markdown("This box plot shows the distribution of the selected measure across different hospitals in the selected state.")
            fig_box = px.box(df_value, x='hospital_name', y='value', title=f'{selected_measure} - {selected_reported_measure} Distribution by Hospital')
            st.plotly_chart(fig_box)

        # Heatmap: Value Over Time by Hospital
        if "Heatmap of Values Over Time" in plot_options:
            st.markdown("### Heatmap of Values Over Time")
            st.markdown("This heatmap shows the variation of the selected measure across different hospitals over time.")
            fig_heatmap = px.density_heatmap(df_value, x='hospital_name', y='reportingstartdate', z='value', title=f'Heatmap of {selected_measure} - {selected_reported_measure} Over Time by Hospital')
            st.plotly_chart(fig_heatmap)

        # Hospital Rankings
        if "Ranking of Hospitals" in plot_options:
            st.markdown("### Ranking of Hospitals")
            st.markdown("This bar chart ranks hospitals based on the average value of the selected measure.")
            df_ranked = df_value.groupby('hospital_name').agg({'value': 'mean'}).reset_index().sort_values(by='value', ascending=False)
            fig_bar = px.bar(df_ranked, x='hospital_name', y='value', title=f'Ranking of Hospitals by {selected_measure} - {selected_reported_measure}')
            st.plotly_chart(fig_bar)

        # Scatter Plot for Correlation Analysis
        if "Correlation Analysis" in plot_options:
            st.markdown("### Correlation Analysis")
            st.markdown("This scatter plot shows the correlation between the selected measure and another measure of your choice.")
            another_metric = st.selectbox("Select Another Metric for Correlation", np.sort(df_measures['measurename'].unique()))
            sql_query_another_metric = f'''
            SELECT
                info.value,
                ds.reportingstartdate,
                info.reportingunitcode,
                h.name as hospital_name
            FROM
                datasets ds
            JOIN
                measurements m ON ds.measurecode = m.measurecode
            JOIN
                reported_measurements rm ON ds.reportedmeasurecode = rm.reportedmeasurecode
            JOIN
                info ON ds.datasetid = info.datasetid
            JOIN
                hospitals h ON info.reportingunitcode = h.code
            WHERE
                m.measurename = '{another_metric.replace("'", "''")}' AND
                ds.stored = TRUE AND
                h.state = '{safe_state}'
            ORDER BY
                ds.reportingstartdate ASC;
            '''
            df_another_metric = fetch_data(sql_query_another_metric)
            if not df_another_metric.empty:
                df_another_metric = df_another_metric.groupby('reportingstartdate').agg({'value': 'mean'}).reset_index()
                df_correlation = df_value_aggregated.merge(df_another_metric, on='reportingstartdate', suffixes=(f'_{selected_measure}', f'_{another_metric}'))
                fig_scatter = px.scatter(df_correlation, x=f'value_{selected_measure}', y=f'value_{another_metric}', title=f'Correlation Between {selected_measure} and {another_metric}')
                st.plotly_chart(fig_scatter)
        
        # Display the Data Table
        st.markdown("### Data Table")
        st.markdown("This table displays the raw data for the selected measure, including the reporting date, value, and hospital name.")
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.dataframe(df_value[['reportingstartdate', 'value', 'hospital_name']])
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.write("No data found for the selected measure and reported measure.")

    if st.button("Return to Home"):
        st.session_state['page'] = 'home'
        



# hospitals 

def display_hospitals():
    """Display hospitals on a map, as a pie chart, and in a table."""
    st.title("Hospitals")

    st.markdown("""
    ## Explore Australian Hospitals 
    
    This section provides a comprehensive analysis of hospitals across different states. You can visualize the locations of hospitals on an interactive map, explore the distribution of private and public hospitals, and filter hospitals by state and operational status.""")

    if st.button("Return to Home"):
        st.session_state['page'] = 'home'

    # Fetch hospital data from the database
    hospital_df = fetch_data('SELECT Latitude, Longitude, Name, Type, Sector, Open_Closed, State FROM hospitals')
    hospital_df['latitude'] = pd.to_numeric(hospital_df['latitude'])
    hospital_df['longitude'] = pd.to_numeric(hospital_df['longitude'])
    hospital_df.dropna(subset=['latitude', 'longitude'], inplace=True)

    # Display hospitals on a map
    hospital_map = folium.Map(location=[-25, 135], zoom_start=5)
    for _, row in hospital_df.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=row['name']
        ).add_to(hospital_map)
    folium_static(hospital_map)

    # Create a bar chart for the number of private and public hospitals per state
    state_sector_counts = hospital_df.groupby(['state', 'sector']).size().reset_index(name='Number of Hospitals')
    private_hospitals = state_sector_counts[state_sector_counts['sector'] == 'Private']
    public_hospitals = state_sector_counts[state_sector_counts['sector'] == 'Public']
    state_counts = pd.merge(private_hospitals, public_hospitals, on='state', suffixes=('_private', '_public'), how='outer').fillna(0)

    fig_hist = px.bar(state_counts, x='state', y=['Number of Hospitals_private', 'Number of Hospitals_public'], barmode='group',
                      title="Number of Private and Public Hospitals per State", labels={'value': 'Number of Hospitals', 'variable': 'Hospital Type'})
    fig_hist.update_layout(xaxis_title="State", yaxis_title="Count")
    st.plotly_chart(fig_hist)   

    
    excel_file = 'data/Admitted Patients.xlsx'
    xls = pd.ExcelFile(excel_file)

    # Load and clean the data for Table 2.9
    table_2_9_cleaned = pd.read_excel(xls, sheet_name='Table 2.9', header=2)
    table_2_9_cleaned = table_2_9_cleaned.drop(columns=['Average since 2018–19', 'Since 2021–22'])

    # Retain only the rows related to public and private hospitals, up to the "All hospitals" row
    public_hospitals = table_2_9_cleaned.iloc[[1, 2, 3]].copy()
    private_hospitals = table_2_9_cleaned.iloc[[4, 5, 6]].copy()

    # Convert the data to long format for easier plotting
    public_hospitals_long = public_hospitals.melt(id_vars=['Unnamed: 0'], var_name='Year', value_name='Average Length of Stay')
    private_hospitals_long = private_hospitals.melt(id_vars=['Unnamed: 0'], var_name='Year', value_name='Average Length of Stay')

    # Rename the 'Unnamed: 0' column to 'Hospital Type'
    public_hospitals_long = public_hospitals_long.rename(columns={'Unnamed: 0': 'Hospital Type'})
    private_hospitals_long = private_hospitals_long.rename(columns={'Unnamed: 0': 'Hospital Type'})

    # Plot for public hospitals using Plotly
    st.markdown("### Average Length of Stay in Australian Hospitals")
    fig_public = px.bar(public_hospitals_long, x='Year', y='Average Length of Stay', color='Hospital Type',
                        title='Average Length of Stay for Public Hospitals')
    fig_public.update_layout(xaxis_title="Year", yaxis_title="Average Length of Stay (Days)")
    st.plotly_chart(fig_public)

    fig_private = px.bar(private_hospitals_long, x='Year', y='Average Length of Stay', color='Hospital Type',
                         title='Average Length of Stay for Private Hospitals')
    fig_private.update_layout(xaxis_title="Year", yaxis_title="Average Length of Stay (Days)")
    st.plotly_chart(fig_private)


    # Load the Excel file for further analysis
    excel_file = 'data/Admitted Patients.xlsx'
    # Add population data for each state
    population_data = {
        "New South Wales": 7317500,
        "Victoria": 5640900,
        "Queensland": 4599400,
        "Western Australia": 2366900,
        "South Australia": 1659800,
        "Tasmania": 511000,
        "Australian Capital Territory": 366900,
        "Northern Territory": 231200
    }

    # Filter hospitals based on selected state and open/closed status
    selected_state_hospital = st.selectbox("Select State", hospital_df['state'].unique())
    selected_status = st.selectbox("Select Open/Closed", hospital_df['open_closed'].unique())
    st.markdown(f"### Hospitals in {selected_state_hospital}")
    
    filtered_df = hospital_df[(hospital_df['state'] == selected_state_hospital) & (hospital_df['open_closed'] == selected_status)]
    
    # Display population and hospital statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        population = population_data.get(selected_state_hospital, "N/A")
        st.metric(label="Population", value=f"{population:,}" if population != "N/A" else population)

    with col2:
        total_hospitals = len(filtered_df)
        st.metric(label="Total Number of Hospitals", value=total_hospitals)

    with col3:
        # Use float division to calculate the ratio
        ratio = (total_hospitals / population) * 1000 if population != "N/A" else "N/A"
        st.metric(label="Hospitals per 1,000 Population", value=f"{ratio:.2f}" if ratio != "N/A" else ratio)

    # Plot the map and pie chart
    col1, col2 = st.columns(2)

    with col1:  
        if not filtered_df.empty:
            fig_map = px.scatter_mapbox(
                filtered_df,
                lat="latitude",
                lon="longitude",
                hover_name="name",
                color="sector",
                zoom=4,
                height=500,
                color_discrete_map={'Public': 'blue', 'Private': 'light blue'}
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map)
        else:
            st.write("No hospitals found with the selected criteria.")

    with col2:
        sector_counts = filtered_df['sector'].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Count']

        fig_pie = px.pie(sector_counts, names='Sector', values='Count', title=f"Total number of hospitals in {selected_state_hospital}")
        st.plotly_chart(fig_pie)


# budget 
        
def display_budget():
    # Define the file path
    file_path = 'data/Expediture.xlsx'
    st.title("Budget")
    # Load the Excel file
    xls = pd.ExcelFile(file_path)

    # Load and clean the specific sheet "Table 1"
    df_table_1 = pd.read_excel(xls, 'Table 1')
    df_cleaned_1 = df_table_1.drop([0, 1]).reset_index(drop=True)
    df_cleaned_1.columns = ['Year', 'Current_Price', 'Constant_Price', 'NaN1', 'Nominal_Change', 'Real_Growth']
    df_cleaned_1 = df_cleaned_1.drop(columns=['NaN1'])
    df_cleaned_1['Current_Price'] = pd.to_numeric(df_cleaned_1['Current_Price'], errors='coerce')
    df_cleaned_1['Constant_Price'] = pd.to_numeric(df_cleaned_1['Constant_Price'], errors='coerce')
    df_cleaned_1['Nominal_Change'] = pd.to_numeric(df_cleaned_1['Nominal_Change'], errors='coerce')
    df_cleaned_1['Real_Growth'] = pd.to_numeric(df_cleaned_1['Real_Growth'], errors='coerce')

    # Use only the first 10 rows (excluding the first row with NaNs)
    df_cleaned_1 = df_cleaned_1[1:11].reset_index(drop=True)

    # Display the data in a table
    st.write("### Health Spending")

    fig1 = px.line(df_cleaned_1, x='Year', y=['Current_Price', 'Constant_Price'], 
                   labels={'value': 'Amount ($ million)', 'variable': 'Type'}, 
                   title='Total Health Spending in Current and Constant Prices')

    fig2 = px.line(df_cleaned_1, x='Year', y=['Nominal_Change', 'Real_Growth'], 
                   labels={'value': 'Percentage (%)', 'variable': 'Type'}, 
                   title='Annual Rates of Change')

    st.plotly_chart(fig1)
    st.plotly_chart(fig2)

    # Load and clean the specific sheet "Table 4"
    df_table_4 = pd.read_excel(xls, 'Table 4')

    # Remove unnecessary rows and columns
    df_table_4 = df_table_4.iloc[1:12].reset_index(drop=True)
    df_table_4.columns = ['Year', 'NSW', 'NSW_NaN', 'VIC', 'VIC_NaN', 'QLD', 'QLD_NaN', 'SA', 'SA_NaN', 'WA', 'WA_NaN', 
                          'TAS', 'TAS_NaN', 'ACT', 'ACT_NaN', 'NT', 'NT_NaN', 'Australia']
    df_table_4 = df_table_4[['Year', 'NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'ACT', 'NT', 'Australia']]
    
    # Convert numeric columns to proper numeric types
    cols = df_table_4.columns.drop('Year')
    df_table_4[cols] = df_table_4[cols].apply(pd.to_numeric, errors='coerce')

    # Display dropdown menu for state selection
    state = st.selectbox('Select a State/Territory', df_table_4.columns[1:-1])

    # Plot the data for the selected state
    fig3 = px.line(df_table_4, x='Year', y=state, 
                   labels={'value': 'Amount ($ million)', 'variable': 'Type'}, 
                   title=f'Total Health Spending in Constant Prices for {state} (2011-12 to 2021-22)')

    st.plotly_chart(fig3)

    df_table_7 = pd.read_excel(xls, 'Table 7')
    df_table_7_cleaned = df_table_7.iloc[2:13, [0, 4, 6]].reset_index(drop=True)
    df_table_7_cleaned.columns = ['Year', 'GDP', 'Health_to_GDP_Ratio']

    # Clean the 'Year' column to handle the '2011–12' format
    df_table_7_cleaned['Year'] = df_table_7_cleaned['Year'].apply(lambda x: x.split('–')[0]).astype(int)
    df_table_7_cleaned['GDP'] = pd.to_numeric(df_table_7_cleaned['GDP'], errors='coerce')
    df_table_7_cleaned['Health_to_GDP_Ratio'] = pd.to_numeric(df_table_7_cleaned['Health_to_GDP_Ratio'], errors='coerce')

    # Plot GDP over time
    fig_gdp = px.line(df_table_7_cleaned, x='Year', y='GDP', 
                      labels={'GDP': 'GDP ($ million)'}, 
                      title='GDP in Australia Over Time')

    # Plot Health Spending to GDP Ratio over time
    fig_ratio = px.line(df_table_7_cleaned, x='Year', y='Health_to_GDP_Ratio', 
                        labels={'Health_to_GDP_Ratio': 'Health Spending to GDP Ratio (%)'}, 
                        title='Health Spending to GDP Ratio Over Time')

    st.plotly_chart(fig_gdp)
    st.plotly_chart(fig_ratio)



# Contact us 
    
def display_contactus():
    st.title("Contact Us")

    st.write("""
    We are here to assist you with any questions, concerns, or feedback you may have. Please feel free to reach out to us via email.
    """)

    # Display contact information
    st.write("**Sonia Borsi**")
    st.write("[Sonia Borsi](mailto:sonia.borsi@studenti.unitn.it) | [Linkedin](https://www.linkedin.com/in/sonia-borsi-824998260/)")
    st.write("**Filippo Costamagna**")
    st.write("[Filippo.costamagna](mailto:filippo.costamagna@studenti.unitn.it) | [Linkedin](https://www.linkedin.com/in/filippo-costamagna-a439b3303/)")

    st.write("""
    We look forward to hearing from you and will respond as soon as possible.
    """)

    st.markdown("#### Learn more")

    # Markdown with a link that opens in a new tab
    st.markdown(
        """
        <a href="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation.git" target="_blank" style="text-decoration: none;">
            <button style="display: block; width: 100%; padding: 10px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; text-align: center; font-size: 16px; cursor: pointer;">
                Visit our repository
            </button>
        </a>
        """,
        unsafe_allow_html=True
)





# Main Function
def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'

    page = setup_sidebar()  # Setup sidebar and store the selected page

    if page == 'Home':
        display_home_page()
    elif page == 'Measures':
        display_measures()
    elif page == 'Hospitals':
        display_hospitals()
    elif page == 'Budget':
        display_budget()
    elif page == 'Contact us':
        display_contactus()


if __name__ == '__main__':
    main()