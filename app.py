import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import iplot
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from datetime import date, timedelta
import io
import matplotlib.pyplot as plt
from metpy.plots import SkewT
from metpy.units import units
from metpy.calc import wind_components
from metpy.units import units


def download_dataframe_as_xlsx(dataframe, button_text="Download as XLSX"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, sheet_name='Sheet1', index=False)
    output.seek(0)
    button = st.download_button(label=button_text, data=output, file_name='Absolute Data.xlsx', key="download_button")
    return button
def download_average_as_xlsx(dataframe, button_text="Download as XLSX"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, sheet_name='Sheet1', index=False)
    output.seek(0)
    button = st.download_button(label=button_text, data=output, file_name='Average Data.xlsx', key="downloader")
    return button

# Function to retrieve data from URL
@st.cache_data(show_spinner=False)
def fetch_data(dat):
 with st.spinner("Loading..."):
    my_options = webdriver.ChromeOptions()
    my_options.add_argument("--headless")
    # browser = webdriver.Chrome(ChromeDriverManager().install(), options=my_options)
    browser = webdriver.Chrome(options=my_options)

    browser.get(dat)

    data_list = []

    for i in range(1, 124, 2):
        xpath = f'/html/body/pre[{i}]'
        try:
            element = browser.find_element(By.XPATH, xpath)
            data = element.text.split('\n')
            data_list.extend(data)
        except:
            break

    browser.quit()

    table_data = []
    for row in data_list:
        columns = row.split()
        if len(columns) == 11:
            table_data.append(columns)

    df = pd.DataFrame(table_data,
                      columns=['PRES', 'HGHT', 'TEMP', 'DWPT', 'RELH', 'MIXR', 'DRCT', 'SKNT', 'THTA', 'THTE', 'THTV'])

    return df

def display(selected, df,avg_df):
    if selected == "Data":


        datatype=st.radio("Select The Data Type",["Absolute","Average"])
        if datatype=="Average":
            st.write("Average Data")
            st.dataframe(avg_df)
            avg_download = download_average_as_xlsx(avg_df, button_text="Download Average Data")
            for column in df.columns:
                min_val = df[column].min()
                max_val = df[column].max()
                print(f"Column '{column}': Min = {min_val}, Max = {max_val}")
        if datatype=="Absolute":
            st.markdown("Absolute Data")
            st.dataframe(df)
            download_button = download_dataframe_as_xlsx(df, button_text="Download Absolute Data")





    elif selected == "Plots":
        xaxis = st.selectbox("Selected the X-Axis", options=df.columns)
        yaxis = st.selectbox("Selected the Y-Axis", options=df.columns)
        plot=px.line(df, x=xaxis, y=yaxis,markers=True)

        if yaxis == "PRES":
            plot.update_layout(yaxis=dict(autorange="reversed"), xaxis_title=xaxis, yaxis_title=yaxis)

        st.plotly_chart(plot)
    elif selected =="Average plots":

        xaxis = st.selectbox("Selected the X-Axis", options=avg_df.columns)
        yaxis = st.selectbox("Selected the Y-Axis", options=avg_df.columns)
        plot = px.scatter(avg_df, x=xaxis, y=yaxis)
        plot.update_traces(
            marker=dict(size=10),  # Set scatter point width
            marker_color='red'  # Set scatter point color
        )
        fullplot=plot.add_trace(px.line(avg_df, x=xaxis, y=yaxis, title='Line').data[0])
        # Customize line plot appearance
        fullplot.update_traces(
            line=dict(width=4)  # Set line width

        )
        if yaxis == "Pressure":
            plot.update_layout(yaxis=dict(autorange="reversed"), xaxis_title=xaxis, yaxis_title=yaxis)
        st.plotly_chart(plot,use_container_width=True)

    elif selected == "Wind Plot":
        create_skewt_plot(avg_df)

def create_skewt_plot(df, figsize=(6, 6), dpi=50):
    # Check if the column names match the expected names
    if 'Pressure' in df.columns and 'Avg Wind Direction' in df.columns and 'Avg Wind Speed' in df.columns:
        # Extract data columns
        pressure_str = df['Pressure'].values
        pressure = [float(p) for p in pressure_str]  # Convert pressure values to floats
        df['Pressure'] = pressure * units('hPa')  # Attach units to pressure

        # Rest of the function remains the same
        wind_dir_degrees = df['Avg Wind Direction'].values
        wind_speed = df['Avg Wind Speed'].values

        # Convert wind direction from degrees to radians
        wind_dir_radians = np.radians(wind_dir_degrees)

        # Attach units to wind_speed
        wind_speed = wind_speed * units('m/s')

        # Calculate u and v components
        u, v = wind_components(wind_speed, wind_dir_radians)

        # Create a new figure with custom dimensions and DPI
        fig = plt.figure(figsize=figsize, dpi=dpi)

        skew = SkewT(fig)

        # Plot wind barbs
        skew.plot_barbs(pressure, u, v)

        # Remove x-axis
        skew.ax.set_xlabel('')

        # Set the y-axis limits to display the entire pressure range
        skew.ax.set_ylim(np.max(pressure), np.min(pressure))

        # Add titles and labels
        plt.title('Skew-T Log-P Diagram')
        plt.xlabel('Temperature (°C)')
        plt.ylabel('Pressure (hPa)')

        # Show the plot
        plt.grid(True, linestyle='--', alpha=0.6)

        st.pyplot(fig)
        st.set_option('deprecation.showPyplotGlobalUse', False)
    else:
        st.warning("The required columns (Pressure, Avg Wind Direction, Avg Wind Speed) are not present in the DataFrame.")

def comp_display(selected, year_dataframes,avg_dataframes):
    if selected == "Data":
        datatype=st.radio("Select The Data Type",["Absolute","Average"])
        if datatype=='Absolute':
            st.markdown("Absolute Data")
            for year, df in year_dataframes.items():
                st.write(f"Data for {year}")
                st.dataframe(df)
            # download_button = download_dataframe_as_xlsx(df, button_text="Download Absolute Data")
        if datatype=='Average':
            st.markdown("Average Data")

            # avg_download = download_average_as_xlsx(avg_df, button_text="Download Average Data")
            for year, avg_df in avg_dataframes.items():
                st.write(f"Data for {year}")
                st.dataframe(avg_df)

    if selected == "Average Plot":
        option=['Pressure', 'Avg Height', 'Avg Temperature', 'Avg Relative Humidity', 'Avg Dew Point', 'Avg Wind Speed', 'Avg Wind Direction']
        xaxis = st.selectbox("Selected the X-Axis", options=option)
        yaxis = st.selectbox("Selected the Y-Axis", options=option)

        plot = go.Figure()
        for year, avg_df in avg_dataframes.items():
            plot.add_trace(go.Scatter(
                x=avg_df[xaxis],
                y=avg_df[yaxis],
                name=year
            ))
            if yaxis == "Pressure":
                plot.update_layout(yaxis=dict(autorange="reversed"), xaxis_title=xaxis, yaxis_title=yaxis)
        plot.update_traces(
            marker=dict(size=10),  # Set scatter point width

        )
        plot.update_traces(
            line=dict(width=4)  # Set line width

        )
        st.plotly_chart(plot,use_container_width=True)



# Function to fetch data for a specific year by month
def for_year(selected_year, stnumber):
    data_list = []
    td = datetime.date.today()
    for m in range(1, 13):
        # Define the end day based on the month
        if m == 2:
            if (selected_year % 4 == 0 and selected_year % 100 != 0) or (selected_year % 400 == 0):
                end_day = 29  # Leap year
            else:
                end_day = 28  # Non-leap year
        elif m in [4, 6, 9, 11]:
            end_day = 30
        else:
            end_day = 31

        # Define the URL for the month
        url = f"https://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={selected_year}&MONTH={m:02d}&FROM=0100&TO={end_day}12&STNM={stnumber}"
        df = fetch_data(url)
        data_list.append(df)

    final_df = pd.concat(data_list, ignore_index=True)
    st.sidebar.title("Options")
    selecte = st.sidebar.selectbox("Please Select", options=['Data','Average plots'])
    avgs = calculate_averages(final_df)
    display(selecte, final_df,avgs)


def for_month(selected_year, stnumber,m):


    if m == 2:
        if (selected_year % 4 == 0 and selected_year % 100 != 0) or (selected_year % 400 == 0):
            end_day = 29  # Leap year
        else:
            end_day = 28  # Non-leap year
    elif m in [4, 6, 9, 11]:
        end_day = 30
    else:
        end_day = 31

        url=f"https://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={selected_year}&MONTH={m}&FROM=0100&TO={end_day}12&STNM={stnumber}"
        df = fetch_data(url)

    st.sidebar.title("Options")
    selecte = st.sidebar.selectbox("Please Select", options=option)
    avgs = calculate_averages(df)
    display(selecte,df,avgs)

@st.cache_data(show_spinner=False)
def compyear(selected_year,stnumber):

        data_list = []
        td = datetime.date.today()
        for m in range(1, 13):
            # Define the end day based on the month
            if m == 2:
                if (selected_year % 4 == 0 and selected_year % 100 != 0) or (selected_year % 400 == 0):
                    end_day = 29  # Leap year
                else:
                    end_day = 28  # Non-leap year
            elif m in [4, 6, 9, 11]:
                end_day = 30
            else:
                end_day = 31

            # Define the URL for the month
            url = f"https://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={selected_year}&MONTH={m:02d}&FROM=0100&TO={end_day}12&STNM={stnumber}"
            df = fetch_data(url)
            data_list.append(df)

        final_df = pd.concat(data_list, ignore_index=True)

        avgs = calculate_averages(final_df)
        return final_df,avgs


@st.cache_data(show_spinner=False)
def calculate_averages(df):
    headers = ['Pressure', 'Avg Height', 'Avg Temperature', 'Avg Relative Humidity', 'Avg Dew Point', 'Avg Wind Speed', 'Avg Wind Direction']
    avg_df = pd.DataFrame(columns=headers)

    # Define the pressure levels
    pres_levels = ['1000.0', '975.0', '950.0', '925.0', '850.0', '700.0', '600.0', '500.0', '400.0', '300.0','200.0','100.0','50.0', '30.0', '20.0', '10.0']

    avg_rows = []  # List to store rows

    for pressure in pres_levels:
        temp = df[df['PRES'] == pressure]
        if not temp.empty:
            avg_height = temp['HGHT'].astype(float).mean()
            avg_temp = temp['TEMP'].astype(float).mean()
            avg_relh = temp['RELH'].astype(float).mean()
            avg_dwpt = temp['DWPT'].astype(float).mean()
            avg_sknt = temp['SKNT'].astype(float).mean()
            avg_drct = temp['DRCT'].astype(float).mean()

            avg_row = {
                'Pressure': pressure,
                'Avg Height': avg_height,
                'Avg Temperature': avg_temp,
                'Avg Relative Humidity': avg_relh,
                'Avg Dew Point': avg_dwpt,
                'Avg Wind Speed': avg_sknt,
                'Avg Wind Direction': avg_drct
            }

            avg_rows.append(avg_row)

    avg_df = pd.concat([avg_df, pd.DataFrame(avg_rows)], ignore_index=True)

    return avg_df



# Streamlit setup
st.set_page_config(page_title="Meteoplot", page_icon="🌧", layout="wide")
st.title("Meteoplot :barely_sunny:",anchor=False)


switch=st.sidebar.toggle("Comparison")



if switch:
    stnumber=st.sidebar.number_input("Enter Station Number",step=1,value=43279)
    comoption=st.sidebar.selectbox("Select Comparison Type",options=["Day","Month","Year"])
    if comoption=="Month":
        # Create a dictionary to store data frames for corresponding years
        year_dataframes = {}
        avg_dataframes={}

        ty = datetime.date.today()
        tyy=ty.year
        # years = st.slider("Select The Years", 1973, ty.year, (ty.year-3, ty.year-1))
        yearop=list(range(1973,ty.year+1))
        yearop.insert(0,'Select Year')
        year0=st.selectbox("Select The Start Year",yearop)
        if not year0=='Select Year':
            year1=st.selectbox("Select The End Year",range(year0+1,ty.year))
            monoptions = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            months = st.selectbox("Select Month", options=monoptions)
            monindex = monoptions.index(months) + 1


            for selected_year in range(year0, year1+ 1):
                if monindex == 2:
                    if (selected_year % 4 == 0 and selected_year % 100 != 0) or (selected_year % 400 == 0):
                        end_day = 29  # Leap year
                    else:
                        end_day = 28  # Non-leap year
                elif monindex in [4, 6, 9, 11]:
                    end_day = 30
                else:
                    end_day = 31
                url = f"https://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={selected_year}&MONTH={monindex}&FROM=0100&TO={end_day}12&STNM={stnumber}"
                df = fetch_data(url)
                avg_df=calculate_averages(df)
                # Store the data frame in the dictionary under the corresponding year
                year_dataframes[selected_year] = df
                avg_dataframes[selected_year]=avg_df



            selecte = st.sidebar.selectbox("Please Select", options=['Data','Average Plot'])
            comp_display(selecte,year_dataframes,avg_dataframes)



    elif comoption=="Day":
        # Create a dictionary to store data frames for corresponding years
        year_dataframes = {}
        avg_dataframes = {}
        ty=datetime.date.today()
        yearop=list(range(1973,ty.year))
        yearop.insert(0,'Select Year')
        year0=st.selectbox("Select The Start Year",yearop)
        if not year0=='Select Year':
            year1=st.selectbox("Select The End Year",range(year0+1,ty.year+1))

            daycom=st.date_input("Select Date",date.today())
            date=daycom.day
            month=daycom.month
            for this_year in range(year0,year1+1):
                url = f"https://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={this_year}&MONTH={month}&FROM={date}00&TO={date}12&STNM={stnumber}"
                df = fetch_data(url)
                avg_df = calculate_averages(df)
                # Store the data frame in the dictionary under the corresponding year
                year_dataframes[this_year] = df
                avg_dataframes[this_year] = avg_df

            option = ["Data", "Plots", "Average plots", "Wind Plot"]

            selecte = st.sidebar.selectbox("Please Select", options=['Data','Average Plot'])
            comp_display(selecte, year_dataframes, avg_dataframes)
    elif comoption=="Year":


        # Create empty dictionaries to store data frames
        year_dataframes = {}
        avg_dataframes = {}

        ty = datetime.date.today()
        yearop = list(range(1973, ty.year))
        yearop.insert(0, 'Select Year')
        year0 = st.selectbox("Select The Start Year", yearop)

        if not year0 == 'Select Year':
            year1 = st.selectbox("Select The End Year", range(year0 + 1, ty.year + 1))

            for this_year in range(year0, year1 + 1):
                df,avg_df = compyear(this_year, stnumber)



                # Store the data frame in the dictionary under the corresponding year
                year_dataframes[this_year] = df

                avg_dataframes[this_year] = avg_df

        selecte = st.sidebar.selectbox("Please Select", options=['Data', 'Average Plot'])
        comp_display(selecte, year_dataframes, avg_dataframes)







else:

    option = ["Data", "Plots", "Average plots","Wind Plot"]


    td = datetime.date.today()
    yr = td.year
    mn = td.month
    datetype = st.sidebar.selectbox("Select Date Type", options=["One Day", "Month", "Specific", "Year"])
    stnumber = st.sidebar.number_input("Enter The Station number", step=1,value=43279)


    if datetype == "One Day":
        date = st.date_input("Please Select The Day")
        tie = st.selectbox("Select The Time", options=["00 UTC", "12 UTC","Both"])
        if tie == "00 UTC":
            time1 = "00"
            time2 = "00"
        if tie == "12 UTC":
            time1 = "12"
            time2 = "12"
        if tie == "Both":
            time1 = "00"
            time2 = "12"
        year = date.year
        month = date.month
        day = date.day
        url = f"https://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={year}&MONTH={month}&FROM={day}{time1}&TO={day}{time2}&STNM={stnumber}"
        df = fetch_data(url)
        st.sidebar.title("Options")
        selected = st.sidebar.selectbox("Please Select", options=option)


        # Calculate averages for the fetched data
        avgs = calculate_averages(df)
        display(selected, df, avgs)



    elif datetype == "Specific":
        startdate = st.date_input("**Enter The Start Date**")

        enddate = st.date_input("Enter The End Date")
        startyear = startdate.year
        startmonth = startdate.month
        startday = startdate.day
        endyear = enddate.year
        endmonth = enddate.month
        endday = enddate.day

        data_list = []

        # Iterate through specific date ranges within the same month
        current_date = startdate
        while current_date <= enddate:
            for time in ["00", "12"]:
                year = current_date.year
                month = current_date.month
                day = current_date.day
                url = f"https://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={year}&MONTH={month}&FROM={day}{time}&TO={day}{time}&STNM={stnumber}"
                df = fetch_data(url)
                data_list.append(df)
            current_date += timedelta(days=1)

        # Concatenate dataframes
        final_df = pd.concat(data_list, ignore_index=True)
        st.sidebar.title("Options")
        selecte = st.sidebar.selectbox("Please Select", options=option)
        # display(selecte, final_df)
        # Calculate averages for the fetched data
        avgs = calculate_averages(final_df)
        display(selecte, final_df, avgs)




    elif datetype == "Year":
        selected_year = st.selectbox("Select The Year", range(1973, yr + 1))
        for_year(selected_year, stnumber)


    elif datetype == "Month":
        mon={"January":1,"Febuary":2,"March":3,"April":4,"May":5,"June":6,"July":7,"August":8,"September":9,"October":10,"November":11,"December":12}
        monoptions = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        selected_month=st.selectbox("Select The Month",options=mon)
        selected_year=st.selectbox("Select Year ",range(1973,yr+1))
        m=mon[selected_month]
        for_month(selected_year,stnumber,m)
