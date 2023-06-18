from datetime import datetime
from time import *
import random
# pip install numpy
import numpy as np
# pip install dash
from dash import Dash ,dcc, html
from dash.dependencies import Input, Output
# pip install plotly
import plotly.express as px
# pip install dash-bootstrap-components
import dash_bootstrap_components as dbc
# pip install pandas
import pandas as pd
# pip install pyserial
import serial

import csv


# set to true if testing without serial
isTesting = True

# ----------setting up serial communicaton---------
#CHANGE COM PORT AND BAUDRATE
COM_PORT = '/dev/cu.usbmodem379B345C35341'
BAUD_RATE = 9600
if(not isTesting):
    ad = serial.Serial(COM_PORT, BAUD_RATE)
    sleep(1)



data = {
    "timestamp":[],
    "velocity": [],
    "altitude": [],
    "pressure":[],
}
df = pd.DataFrame(data)

gps_data = {
    "lat":[12.9716],
    "lon":[77.5946]
}
gpsDF = pd.DataFrame(gps_data)

commStatus = "Connected" if not isTesting else "Disconnected"

filename = "flightData.csv"

logo = "./logo.png"

# update csv file 
def update_csv():
    global df, data, gps_data, gpsDF,commStatus
    toWrie = (np.hstack((df.values[-1],np.array([gpsDF.values[0][0],gpsDF.values[0][1]]))))
    
    # writing to csv file 
    with open(filename, 'a') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        # writing the data rows 
        csvwriter.writerow(toWrie)


#update data with random values
def update_random():
    global df, data
    current_time = datetime.now().time()
    data['timestamp'].append(current_time.strftime("%M:%S"))
    data['velocity'].append(random.randint(0,100))
    data['altitude'].append(random.randint(0,100))
    data['pressure'].append(random.randint(0,100))
    df = pd.DataFrame(data)

#update data with serial values
# assuming data packet is in form : vel,alt,press,lat,lon 
def update_serial():
    global df, data, gps_data, gpsDF,commStatus
    try:
        while (ad.inWaiting()==0):
            pass
        commStatus = "Connected"
        dataPacket=ad.readline()
        dataPacket=str(dataPacket,'utf-8')
        splitPacket=dataPacket.split(",")
        current_time = datetime.now().time()
        data['timestamp'].append(current_time.strftime("%M:%S"))
        data['velocity'].append(float(splitPacket[0]))
        data['altitude'].append(float(splitPacket[1]))
        data['pressure'].append(float(splitPacket[2]))
        gps_data["lat"][0] = float(splitPacket[3])
        gps_data["lon"][0] = float(splitPacket[4])
        df = pd.DataFrame(data)
        gpsDF = pd.DataFrame(gps_data)
    except Exception as e:
        print(e)



# setting up plotly dash
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
px.set_mapbox_access_token("pk.eyJ1IjoiYXNhdHdpazIxOCIsImEiOiJjbGh2bm1lb28wOXB4M2dwN291anoxNmwwIn0.IjyWgNVRj-rLIgdisFBAlg")

#layout 
app.layout =html.Div([
    dbc.Row([

        dbc.Col(html.Div([
            html.Div(id="sidePanel",style={"margin":"20px 20px","height":"100%"})
        ],style={"margin":"20px 20px","height":"100%"}),width={"size":3}),

        dbc.Col([
            dbc.Row([
                dbc.Col(html.H4("ThrustMIT"),className='text-center')
            ]),
            dbc.Row([
                dbc.Col( dcc.Graph(id='velocity-graph'),width=6),
                dbc.Col( dcc.Graph(id='altitude-graph'),width=6),
            ]),
            dbc.Row([
                dbc.Col( dcc.Graph(id='pressure-graph'),width=6),
                dbc.Col( dcc.Graph(id='map-graph'),width=6),
            ]),
            dbc.Row([
                dbc.Col(
                    dcc.Interval(
                        id='interval-component',
                        interval=1*1000, # in milliseconds
                        n_intervals=0
                    )
                )
            ])
        ],width={"size":8})
    ])

   
])

# velocity graph
@app.callback(Output('velocity-graph','figure'),Input('interval-component','n_intervals'))
def update_velocity_graph(n):
    global df

    # updating dataframe
    if(isTesting):
        update_random()
        update_csv()
    else:
        update_serial()
        update_csv()

    fig = px.line(df[["timestamp","velocity"]].tail(20), x="timestamp", y="velocity",markers=True,height=350) 
    fig.update_layout(template="plotly_dark",xaxis_title="time (m:s)",yaxis_title="velocity (m/s)") 
    return fig

# altitude graph
@app.callback(Output('altitude-graph','figure'),Input('interval-component','n_intervals'))
def update_altitude_graph(n):
    global df
    fig = px.line(df[["timestamp","altitude"]].tail(20), x="timestamp", y="altitude",markers=True,height=350)
    fig.update_layout(template="plotly_dark",xaxis_title="time (m:s) ",yaxis_title="altitude (m)") 

    return fig

# pressure graph
@app.callback(Output('pressure-graph','figure'),Input('interval-component','n_intervals'))
def update_pressure_graph(n):
    global df
    fig = px.line(df[["timestamp","pressure"]].tail(20), x="timestamp", y="pressure",markers=True,height=350)  
    fig.update_layout(template="plotly_dark",xaxis_title="time (m:s) ",yaxis_title="pressure (Pa)") 
    return fig

# map
@app.callback(Output('map-graph','figure'),Input('interval-component','n_intervals'))
def update_map_graph(n):
    global gpsDF
    fig = px.scatter_mapbox(gpsDF, lat="lat", lon="lon", size_max=15, zoom=10,height=350)
    fig.update_layout(template="plotly_dark") 
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

# side panel
@app.callback(Output('sidePanel','children'),Input('interval-component','n_intervals'))
def update_velocity_graph(n):
    style = {
        'padding': '10px',
        'margin': '10px',
        'box-shadow': '2px 2px 4px rgb(67, 63, 77)'
    }
    return([
        html.H6("Comm Status : "+commStatus),
        html.H6("Velocity : "+str(df["velocity"].tail(1).values[0])+" m/s",style=style),
        html.H6("Altitude : "+str(df["altitude"].tail(1).values[0])+" m" , style=style),
        html.H6("Pressure : "+str(df["pressure"].tail(1).values[0])+" Pa", style = style),
    ])


if __name__ == '__main__':
    app.run_server(debug=True)