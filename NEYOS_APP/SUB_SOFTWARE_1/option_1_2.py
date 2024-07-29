import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np


# Function to load and parse the CSV file
def load_data(uploaded_file):
    # Read the file into a list of lines
    lines = uploaded_file.read().decode("utf-8").splitlines()

    # Skip the metadata lines
    data_lines = lines[3:]  # Assuming the first 3 lines are metadata

    # Parse the data lines into a DataFrame
    df = pd.DataFrame([line.split(",") for line in data_lines], columns=["SOC(%)", "Open Voltage(V)", "ESR(ohm)"])

    # Convert columns to appropriate data types
    df["SOC(%)"] = pd.to_numeric(df["SOC(%)"])
    df["Open Voltage(V)"] = pd.to_numeric(df["Open Voltage(V)"])
    df["ESR(ohm)"] = pd.to_numeric(df["ESR(ohm)"])

    # Remove the first and last rows
    df = df.iloc[1:-1].reset_index(drop=True)

    return df


# Function to calculate battery voltage over time
def calculate_voltage_over_time(capacity, consumption_below_60, consumption_above_60, esr_below_60, esr_above_60, df):
    time = []
    voltage_with_esr = []
    voltage_without_esr = []
    soc_list_with_esr = []
    soc_list_without_esr = []
    soc_with_esr = 100
    soc_without_esr = 100
    current_capacity_with_esr = capacity
    current_capacity_without_esr = capacity
    t = 0

    time_below_60 = 0
    time_above_60 = 0
    soc_60_crossed = False
    min_voltage = df["Open Voltage(V)"].min()

    while soc_without_esr > 0:  # Continue loop until SOC without ESR reaches 0%
        if soc_with_esr > 60:
            consumption_with_esr = consumption_above_60
            esr = esr_above_60
            if not soc_60_crossed:
                time_above_60 = t
        else:
            consumption_with_esr = consumption_below_60
            esr = esr_below_60
            if not soc_60_crossed:
                soc_60_crossed = True
                time_below_60 = t

        consumption_without_esr = consumption_above_60 if soc_without_esr > 60 else consumption_below_60

        if soc_with_esr > 0:
            current_capacity_with_esr -= consumption_with_esr * (1 / 60)  # Assuming time step is 1 minute
        current_capacity_without_esr -= consumption_without_esr * (1 / 60)

        if current_capacity_with_esr <= 0 and soc_with_esr > 0:
            soc_with_esr = 0
        else:
            soc_with_esr = max((current_capacity_with_esr / capacity) * 100, 0)  # Ensure SOC does not go below 0%

        if current_capacity_without_esr <= 0 and soc_without_esr > 0:
            soc_without_esr = 0
        else:
            soc_without_esr = max((current_capacity_without_esr / capacity) * 100, 0)  # Ensure SOC does not go below 0%

        time.append(t)
        soc_list_with_esr.append(soc_with_esr)
        soc_list_without_esr.append(soc_without_esr)

        # Interpolate voltage with ESR
        if soc_with_esr > 0:
            voltage_open_with_esr = np.interp(soc_with_esr, df["SOC(%)"], df["Open Voltage(V)"])
            voltage_load_with_esr = voltage_open_with_esr - (
                        consumption_with_esr / 1000) * esr  # V = V_open - I*R, converting mA to A
            if voltage_load_with_esr <= min_voltage:
                voltage_with_esr.append(min_voltage)
                soc_with_esr = 0  # Stop if voltage with ESR falls below minimum voltage
            else:
                voltage_with_esr.append(voltage_load_with_esr)
        else:
            voltage_with_esr.append(min_voltage)  # Add minimum voltage if SOC with ESR is 0

        # Interpolate voltage without ESR
        if soc_without_esr > 0:
            voltage_open_without_esr = np.interp(soc_without_esr, df["SOC(%)"], df["Open Voltage(V)"])
            voltage_without_esr.append(voltage_open_without_esr)  # Without ESR effect
        else:
            voltage_without_esr.append(
                np.interp(0, df["SOC(%)"], df["Open Voltage(V)"]))  # Add open voltage at SOC 0% if SOC without ESR is 0

        t += 1

        # Stop the loop if both SOCs reach 0%
        if soc_with_esr == 0 and soc_without_esr == 0:
            break

    total_time_below_60 = t - time_below_60
    total_time = t

    return time, voltage_with_esr, voltage_without_esr, soc_list_with_esr, soc_list_without_esr, time_above_60, total_time_below_60, total_time


# Streamlit layout
st.title("Battery Profile and System Consumption")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Load the data
    df = load_data(uploaded_file)

    # Display the dataframe and plot side by side
    col1, col2 = st.columns(2)

    with col1:
        st.write("Dataframe:")
        st.dataframe(df)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['SOC(%)'], y=df['Open Voltage(V)'], mode='lines+markers', name='Open Voltage'))
        fig.update_layout(
            title='Battery Profile: SOC vs Open Voltage',
            xaxis_title='SOC (%)',
            yaxis_title='Open Voltage (V)'
        )
        st.plotly_chart(fig)

    # Input fields for battery parameters
    st.subheader("Battery and System Parameters")
    capacity = st.number_input("Battery Capacity (mAh)", value=3700)
    consumption_below_60 = st.number_input("Consumption below 60% SOC (mA)", value=100)
    consumption_above_60 = st.number_input("Consumption above 60% SOC (mA)", value=50)
    esr_below_60 = st.number_input("ESR below 60% SOC (ohms)", value=0.046)
    esr_above_60 = st.number_input("ESR above 60% SOC (ohms)", value=0.046)

    # Calculate and plot voltage over time
    if st.button("Calculate Voltage Over Time"):
        time, voltage_with_esr, voltage_without_esr, soc_list_with_esr, soc_list_without_esr, time_above_60, total_time_below_60, total_time = calculate_voltage_over_time(
            capacity, consumption_below_60, consumption_above_60, esr_below_60, esr_above_60, df
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=voltage_with_esr, mode='lines+markers', name='Battery Voltage with ESR',
                                 text=[f'SOC: {soc:.2f}%' for soc in soc_list_with_esr], hoverinfo='text+name'))
        fig.add_trace(
            go.Scatter(x=time, y=voltage_without_esr, mode='lines+markers', name='Battery Voltage without ESR',
                       text=[f'SOC: {soc:.2f}%' for soc in soc_list_without_esr], hoverinfo='text+name'))

        # Add a line to indicate 60% SOC
        fig.add_shape(type="line",
                      x0=0, y0=np.interp(60, df["SOC(%)"], df["Open Voltage(V)"]),
                      x1=max(time), y1=np.interp(60, df["SOC(%)"], df["Open Voltage(V)"]),
                      line=dict(color="Red", width=2, dash="dashdot"),
                      name="60% SOC Indicator")

        # Add annotation for 60% SOC
        fig.add_annotation(x=max(time) / 2, y=np.interp(60, df["SOC(%)"], df["Open Voltage(V)"]),
                           text="60% SOC",
                           showarrow=True,
                           arrowhead=1)

        fig.update_layout(
            title='Battery Voltage Over Time',
            xaxis_title='Time (minutes)',
            yaxis_title='Battery Voltage (V)'
        )
        st.plotly_chart(fig)

        # Convert times to hours for display
        time_above_60_hours = time_above_60 / 60
        time_below_60_hours = total_time_below_60 / 60
        total_time_hours = total_time / 60

        # Display the elapsed times
        st.write(f"Time above 60% SOC: {time_above_60_hours:.2f} hours")
        st.write(f"Time below 60% SOC: {time_below_60_hours:.2f} hours")
        st.write(f"Total time: {total_time_hours:.2f} hours")
