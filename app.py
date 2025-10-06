import os
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import requests
import traceback

# --- Helper Functions (no changes to logic) ---

def parse_location(location_str):
    """Converts the location string from the form into float values."""
    try:
        import json
        bounds = json.loads(location_str)
        ne, sw = bounds['northEast'], bounds['southWest']
        lat, lon = (ne['lat'] + sw['lat']) / 2, (ne['lng'] + sw['lng']) / 2
        return lat, lon
    except (json.JSONDecodeError, TypeError, ValueError):
        try:
            parts = location_str.replace(" ", "").split(',')
            if len(parts) == 2:
                return float(parts[0]), float(parts[1])
            else:
                return None, None 
        except (ValueError, IndexError):
            return None, None


def analyze_precipitation_data(daily_data, target_indices, time_list):
    """
    A dedicated function to analyze rain and wind data and return
    the results dictionary in the requested format.
    """
    precip_list = daily_data.get('precipitation_sum', [])
    wind_list = daily_data.get('wind_speed_10m_max', [])
    
    no_rain_days, light_rain_days, moderate_rain_days, heavy_rain_days = 0, 0, 0, 0
    storm_alert_days = 0
    history = []

    for i in target_indices:
        rain = precip_list[i] if precip_list[i] is not None else 0
        wind = wind_list[i] if wind_list[i] is not None else 0
        
        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{rain:.1f} mm, Wind: {wind:.1f} km/h"})
        
        if rain <= 1.0:
            no_rain_days += 1
        elif 1.0 < rain <= 5.0:
            light_rain_days += 1
        elif 5.0 < rain <= 25.0:
            moderate_rain_days += 1
        else:
            heavy_rain_days += 1
        
        if rain > 20.0 and wind > 40.0:
            storm_alert_days += 1

    total_years = len(target_indices)
    if total_years == 0:
        return {"title": "Rain Probability", "summary_value": "Data Unavailable", "history": []}

    total_rain_prob = ((total_years - no_rain_days) / total_years) * 100
    
    if total_rain_prob <= 10:
        summary_value = f"{total_rain_prob:.0f}% chance of rain"
    else:
        intensities = {"light": light_rain_days, "moderate": moderate_rain_days, "heavy": heavy_rain_days}
        main_intensity = max(intensities, key=intensities.get)
        
        summary_value = f"{total_rain_prob:.0f}% chance of {main_intensity} rain"
        
        storm_prob = (storm_alert_days / total_years) * 100
        if storm_prob > 5:
            summary_value += ". Storm Alert."
    
    return {
        "title": "Rain Analysis",
        "summary_value": summary_value,
        "history": history,
        "history_headers": ["Year", "Details (Rain/Wind)"]
    }


def fetch_historical_data(lat, lon, month, day, variables):
    results = {}
    
    # --- 1. Aggregate all necessary parameters for the API ---
    daily_params = set()
    if 'prob_chuva' in variables:
        daily_params.add("precipitation_sum")
        daily_params.add("wind_speed_10m_max")
    if 'temp_media' in variables:
        daily_params.add("temperature_2m_mean")
    if 'vel_vento' in variables:
        daily_params.add("wind_speed_10m_max")
    if 'sensacao_termica' in variables:
        daily_params.add("apparent_temperature_max")
    if 'nuvens' in variables:
        daily_params.add("cloud_cover_mean")
    if 'indice_uv' in variables:
        daily_params.add("uv_index_max")
    if 'neve' in variables:
        daily_params.add("snowfall_sum")
    if 'humidade' in variables:
        daily_params.add("relative_humidity_2m_mean")
        
    if not daily_params: 
        return {}

    try:
        # --- 2. Make a SINGLE API call with all the data ---
        base_url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat, "longitude": lon, "start_date": "1950-01-01",
            "end_date": f"{datetime.now().year - 1}-12-31",
            "daily": list(daily_params), "timezone": "auto"
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        daily_data = data.get('daily', {})
        time_list = daily_data.get('time', [])
        
        if not time_list: raise ValueError("API did not return time data.")

        target_indices = [i for i, date_str in enumerate(time_list) if date_str.endswith(f"-{month:02d}-{day:02d}")]

        # --- 3. Process each selected card ---

        if 'prob_chuva' in variables:
            results['prob_chuva'] = analyze_precipitation_data(daily_data, target_indices, time_list)
        
        if 'temp_media' in variables:
            temp_list = daily_data.get('temperature_2m_mean', [])
            if not temp_list or all(v is None for v in temp_list):
                 results['temp_media'] = {"title": "Average Temperature", "summary_value": "N/A", "error": "Historical data unavailable.", "history": []}
            else:
                history, total_temp, valid_points = [], 0.0, 0
                for i in target_indices:
                    temp = temp_list[i]
                    if temp is not None:
                        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{temp:.1f} °C"})
                        total_temp += temp
                        valid_points += 1
                media = total_temp / valid_points if valid_points > 0 else 0
                results['temp_media'] = {"title": "Average Temperature", "summary_value": f"{media:.1f} °C", "history": history, "history_headers": ["Year", "Temperature"]}
        
        if 'vel_vento' in variables:
            wind_list = daily_data.get('wind_speed_10m_max', [])
            if not wind_list or all(v is None for v in wind_list):
                results['vel_vento'] = {"title": "Wind Speed", "summary_value": "N/A", "error": "Historical data unavailable.", "history": []}
            else:
                history, total_wind, valid_points = [], 0.0, 0
                for i in target_indices:
                    wind = wind_list[i]
                    if wind is not None:
                        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{wind:.1f} km/h"})
                        total_wind += wind
                        valid_points += 1
                media_vento = total_wind / valid_points if valid_points > 0 else 0
                results['vel_vento'] = {"title": "Wind Speed", "summary_value": f"{media_vento:.1f} km/h", "history": history, "history_headers": ["Year", "Max Wind"]}
        
        if 'sensacao_termica' in variables:
            app_temp_list = daily_data.get('apparent_temperature_max', [])
            if not app_temp_list or all(v is None for v in app_temp_list):
                results['sensacao_termica'] = {"title": "High Feels-Like Temperature", "summary_value": "N/A", "error": "Historical data unavailable.", "history": []}
            else:
                history, total_temp, valid_points = [], 0.0, 0
                for i in target_indices:
                    temp = app_temp_list[i]
                    if temp is not None:
                        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{temp:.1f} °C"})
                        total_temp += temp
                        valid_points += 1
                media_temp = total_temp / valid_points if valid_points > 0 else 0
                results['sensacao_termica'] = {"title": "High Feels-Like Temperature", "summary_value": f"{media_temp:.1f} °C", "history": history, "history_headers": ["Year", "Max Feels-Like"]}
        
        if 'nuvens' in variables:
            cloud_list = daily_data.get('cloud_cover_mean', [])
            if not cloud_list or all(v is None for v in cloud_list):
                results['nuvens'] = {"title": "Cloud Cover", "summary_value": "N/A", "error": "Historical data unavailable.", "history": []}
            else:
                history, total_cover, valid_points = [], 0.0, 0
                for i in target_indices:
                    cover = cloud_list[i]
                    if cover is not None:
                        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{cover:.0f}%"})
                        total_cover += cover
                        valid_points += 1
                media_nuvens = total_cover / valid_points if valid_points > 0 else 0
                results['nuvens'] = {"title": "Cloud Cover", "summary_value": f"{media_nuvens:.0f}%", "history": history, "history_headers": ["Year", "Average Cover"]}

        if 'indice_uv' in variables:
            uv_list = daily_data.get('uv_index_max', [])
            if not uv_list or all(v is None for v in uv_list):
                results['indice_uv'] = {"title": "UV Index", "summary_value": "N/A", "error": "Historical data unavailable.", "history": []}
            else:
                history, total_uv, valid_points = [], 0.0, 0
                for i in target_indices:
                    uv = uv_list[i]
                    if uv is not None:
                        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{uv:.1f}"})
                        total_uv += uv
                        valid_points += 1
                media_uv = total_uv / valid_points if valid_points > 0 else 0
                results['indice_uv'] = {"title": "UV Index", "summary_value": f"{media_uv:.1f}", "history": history, "history_headers": ["Year", "Max UV"]}
        
        if 'neve' in variables:
            snow_list = daily_data.get('snowfall_sum', [])
            if not snow_list or all(v is None for v in snow_list):
                results['neve'] = {"title": "Snowfall", "summary_value": "N/A", "error": "Historical data unavailable.", "history": []}
            else:
                history, total_snow, valid_points = [], 0.0, 0
                for i in target_indices:
                    snow = snow_list[i]
                    if snow is not None and snow > 0:
                        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{snow:.1f} cm"})
                        total_snow += snow
                    valid_points += 1
                
                snow_prob = (len(history) / valid_points) * 100 if valid_points > 0 else 0
                results['neve'] = {"title": "Snowfall", "summary_value": f"{snow_prob:.0f}% chance", "history": history, "history_headers": ["Year", "Snow Accumulation"]}

        if 'humidade' in variables:
            humidity_list = daily_data.get('relative_humidity_2m_mean', [])
            if not humidity_list or all(v is None for v in humidity_list):
                results['humidade'] = {"title": "Humidity", "summary_value": "N/A", "error": "Historical data unavailable.", "history": []}
            else:
                history, total_humidity, valid_points = [], 0.0, 0
                for i in target_indices:
                    humidity = humidity_list[i]
                    if humidity is not None:
                        history.append({"year": int(time_list[i].split('-')[0]), "value": f"{humidity:.0f}%"})
                        total_humidity += humidity
                        valid_points += 1
                media_humidity = total_humidity / valid_points if valid_points > 0 else 0
                results['humidade'] = {"title": "Humidity", "summary_value": f"{media_humidity:.0f}%", "history": history, "history_headers": ["Year", "Average Humidity"]}

    except Exception as e:
        print("--- ERROR FETCHING DATA ---"); traceback.print_exc()
        for var in variables: 
            if var not in results:
                results[var] = {"title": "Error", "summary_value": "Failure", "error": "Could not retrieve data."}
            
    return results

# --- Flask Web Server Logic ---
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24) 

@app.route('/')
@app.route('/map')
def map_page():
    session.clear()
    return render_template('map-selection.html')

@app.route('/data_selection')
def data_selection_page():
    if 'location' not in session or 'date' not in session: return redirect(url_for('map_page'))
    return render_template('data-selection.html')
    
@app.route('/results')
def results_page():
    if 'data_selections' not in session: return redirect(url_for('data_selection_page'))
    
    location_str = session.get('location', '')
    date_str = session.get('date')
    selections = session.get('data_selections', [])

    if not location_str or not date_str:
        return redirect(url_for('map_page'))

    lat, lon = parse_location(location_str)
    if lat is None or lon is None:
        # Redirect if coordinates are invalid, preventing a crash
        return redirect(url_for('map_page'))

    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    month, day = date_obj.month, date_obj.day
    
    final_results = fetch_historical_data(lat, lon, month, day, selections)
    
    # Ensures the cards are displayed in the order the user selected them
    ordered_results = {key: final_results[key] for key in selections if key in final_results}
    
    return render_template('results.html', date=date_str, location=location_str, results=ordered_results)

@app.route('/save_location', methods=['POST'])
def save_location():
    session['location'] = request.form.get('coordinates')
    session['date'] = request.form.get('event-date')
    return redirect(url_for('data_selection_page'))

@app.route('/process_data', methods=['POST'])
def process_data():
    session['data_selections'] = request.form.getlist('data')
    return redirect(url_for('results_page'))

if __name__ == '__main__':
    app.run(debug=True)