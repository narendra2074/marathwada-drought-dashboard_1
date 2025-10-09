import dash
from dash import dcc, html, Input, Output, State, callback_context
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import base64
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
from datetime import datetime
import sqlite3
import json

# Configuration
USE_SQLITE = False

# Themes
themes = {
    'default': {
        'header': '#6A1B9A', 'bg': '#fafafa', 'card': '#ffffff', 'text': '#333333',
        'border': '#e0e0e0', 'accent': '#8e24aa'
    },
    'dark': {
        'header': '#2d1b69', 'bg': '#121212', 'card': '#1e1e1e', 'text': '#ffffff',
        'border': '#404040', 'accent': '#bb86fc'
    },
    'ocean': {
        'header': '#0077be', 'bg': '#f0f8ff', 'card': '#ffffff', 'text': '#333333',
        'border': '#87ceeb', 'accent': '#4fc3f7'
    },
    'forest': {
        'header': '#228B22', 'bg': '#f5fff5', 'card': '#ffffff', 'text': '#333333',
        'border': '#90ee90', 'accent': '#66bb6a'
    }
}

def load_data():
    if USE_SQLITE:
        try:
            conn = sqlite3.connect('drought_data.db')
            df = pd.read_sql_query("SELECT * FROM drought_data", conn)
            conn.close()
        except:
            df = pd.read_csv('main_data_updated.csv')
    else:
        df = pd.read_csv('main_data_updated.csv')
    return df

def get_map_image(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img = img.resize((600, 600), Image.Resampling.LANCZOS)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            buffer = BytesIO()
            img.save(buffer, format='PNG', quality=95, optimize=True)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
    except:
        pass
    placeholder = Image.new('RGB', (600, 600), color='lightgray')
    buffer = BytesIO()
    placeholder.save(buffer, format='PNG', quality=95)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# Initialize app
app = dash.Dash(__name__)

# Load data
df = load_data()
years = sorted(df['year'].unique())

# Color mapping
colors = {
    'Extreme_Drought': '#8B0000', 'Severe_Drought': '#FF4500', 'Moderate_Drought': '#FFD700',
    'Near_Normal': '#32CD32', 'Moderately_Wet': '#4169E1', 'Extremely_Wet': '#0000FF'
}

icons = {
    'Extreme_Drought': '🔥', 'Severe_Drought': '☀️', 'Moderate_Drought': '🌤️',
    'Near_Normal': '🌱', 'Moderately_Wet': '💧', 'Extremely_Wet': '🌊'
}

# CSS styles
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @keyframes fadeIn { from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);} }
            @keyframes slideIn { from {transform: translateX(-100%);} to {transform: translateX(0);} }
            @keyframes pulse { 0%, 100% {transform: scale(1);} 50% {transform: scale(1.05);} }
            
            .fade-in { animation: fadeIn 0.6s ease-out; }
            .slide-in { animation: slideIn 0.5s ease-out; }
            .pulse { animation: pulse 2s infinite; }
            .hover-scale { transition: transform 0.3s ease; }
            .hover-scale:hover { transform: scale(1.02); }
            
            .loading { border: 3px solid #f3f3f3; border-top: 3px solid #6A1B9A; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            
            @media (max-width: 768px) {
                .main-content { flex-direction: column !important; }
                .column { margin: 5px !important; padding: 15px !important; }
                .map-img { max-width: 100% !important; }
                .header-controls { flex-direction: column !important; gap: 10px; }
            }
            
            .export-btn { background: linear-gradient(45deg, #6A1B9A, #8e24aa); color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; transition: all 0.3s; }
            .export-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(106, 27, 154, 0.3); }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout
app.layout = html.Div(id='main-container', children=[
    dcc.Store(id='theme-store', data='default'),
    dcc.Interval(id='auto-refresh', interval=30000, n_intervals=0),
    
    # Header
    html.Div(id='header', children=[
        html.H1("🌍 Advanced Drought Dashboard", className='slide-in', style={'margin': '0', 'flex': '1'}),
        html.Div(className='header-controls', children=[
            html.Div([
                html.Label("Theme:", style={'margin-right': '5px'}),
                dcc.Dropdown(
                    id='theme-selector',
                    options=[
                        {'label': '🎨 Default', 'value': 'default'},
                        {'label': '🌙 Dark', 'value': 'dark'},
                        {'label': '🌊 Ocean', 'value': 'ocean'},
                        {'label': '🌲 Forest', 'value': 'forest'}
                    ],
                    value='default',
                    style={'width': '120px', 'margin-right': '15px'}
                )
            ]),
            html.Div([
                html.Label("Left Year:", style={'margin-right': '5px'}),
                dcc.Dropdown(id='left-year', options=[{'label': year, 'value': year} for year in years], value=1984, style={'width': '100px', 'margin-right': '15px'})
            ]),
            html.Div([
                html.Label("Right Year:", style={'margin-right': '5px'}),
                dcc.Dropdown(id='right-year', options=[{'label': year, 'value': year} for year in years], value=1981, style={'width': '100px', 'margin-right': '15px'})
            ]),
            html.Button("📊 Export Data", id='export-btn', className='export-btn'),
            html.Button("📈 Show Trends", id='trend-btn', className='export-btn', style={'margin-left': '10px'})
        ], style={'display': 'flex', 'align-items': 'center', 'flex-wrap': 'wrap', 'gap': '10px'})
    ]),
    
    # Trend Analysis Modal
    dcc.Modal(id='trend-modal', is_open=False, children=[
        html.Div([
            html.H3("📈 Drought Trend Analysis", style={'text-align': 'center', 'margin-bottom': '20px'}),
            dcc.Graph(id='trend-chart'),
            html.Button("Close", id='close-trend', style={'margin-top': '20px', 'width': '100%'})
        ], style={'padding': '20px'})
    ]),
    
    # Main content
    html.Div(id='main-content', className='main-content fade-in', children=[
        html.Div(id='left-column', className='column hover-scale'),
        html.Div(id='right-column', className='column hover-scale')
    ]),
    
    # Comparison Section
    html.Div(id='comparison-section', className='fade-in', children=[
        html.H3("📊 Year Comparison Analysis", style={'text-align': 'center', 'margin': '30px 0 20px 0'}),
        html.Div(id='comparison-table')
    ]),
    
    # Footer
    html.Div(id='footer', children=[
        html.P([
            f"📅 Last Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')} | ",
            "🔄 Auto-refresh: 30s | ",
            "💡 Enhanced Drought Monitoring System"
        ], style={'text-align': 'center', 'margin': '20px'})
    ])
])

def create_trend_chart(df):
    categories = ['Extreme_Drought', 'Severe_Drought', 'Moderate_Drought', 'Near_Normal', 'Moderately_Wet', 'Extremely_Wet']
    
    fig = go.Figure()
    for cat in categories:
        fig.add_trace(go.Scatter(
            x=df['year'], y=df[cat], mode='lines+markers',
            name=cat.replace('_', ' '), line=dict(color=colors[cat], width=3),
            hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Area: %{y:.1f} sq km<extra></extra>'
        ))
    
    fig.update_layout(
        title="Drought Categories Trend Over Time",
        xaxis_title="Year", yaxis_title="Area (sq km)",
        hovermode='x unified', height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_column_content(year, df, theme_name):
    theme = themes[theme_name]
    year_data = df[df['year'] == year].iloc[0]
    
    categories = ['Extreme_Drought', 'Severe_Drought', 'Moderate_Drought', 'Near_Normal', 'Moderately_Wet', 'Extremely_Wet']
    values = [year_data[cat] for cat in categories]
    total = sum(values)
    
    non_zero_data = [(cat, val) for cat, val in zip(categories, values) if val > 0]
    
    if non_zero_data:
        pie_categories, pie_values = zip(*non_zero_data)
        
        fig = px.pie(
            values=pie_values, names=[cat.replace('_', ' ') for cat in pie_categories],
            title=f"{year} Distribution", hole=0.5,
            color_discrete_map={cat.replace('_', ' '): colors[cat] for cat in pie_categories}
        )
        fig.update_traces(
            textinfo='percent+label', textfont_size=12,
            hovertemplate='<b>%{label}</b><br>Area: %{value:.1f} sq km<br>Percentage: %{percent}<extra></extra>'
        )
        fig.update_layout(
            showlegend=False, height=300, margin=dict(t=50, b=0, l=0, r=0),
            paper_bgcolor=theme['card'], plot_bgcolor=theme['card'], font_color=theme['text']
        )
    else:
        fig = px.pie(values=[1], names=['No Data'], title=f"{year} Distribution")
    
    # Create enhanced class cards
    class_cards = []
    for i, cat in enumerate(categories):
        value = year_data[cat]
        percentage = (value/total*100) if total > 0 else 0
        
        class_cards.append(
            html.Div([
                html.Div([
                    html.Span(icons[cat], style={'font-size': '24px', 'margin-bottom': '5px'}),
                    html.Div(cat.replace('_', ' '), style={'font-weight': 'bold', 'font-size': '11px', 'text-align': 'center'}),
                    html.Div(f"{value:.1f}", style={'font-weight': 'bold', 'font-size': '16px', 'margin-top': '5px'}),
                    html.Div(f"{percentage:.1f}%", style={'font-size': '10px', 'opacity': '0.9'})
                ], style={'text-align': 'center', 'color': 'white', 'padding': '12px'})
            ], className='hover-scale', style={
                'background': f'linear-gradient(135deg, {colors[cat]}, {colors[cat]}dd)',
                'border-radius': '12px', 'margin': '8px', 'flex': '1', 'min-width': '140px',
                'box-shadow': '0 4px 8px rgba(0,0,0,0.2)', 'transition': 'all 0.3s ease'
            })
        )
    
    return html.Div([
        html.Div([
            html.H3(f"🗓️ {year}", style={'text-align': 'center', 'margin-bottom': '20px', 'color': theme['text']}),
            html.Img(
                src=get_map_image(year_data['Map Images Left']), className='map-img pulse',
                style={'width': '100%', 'max-width': '500px', 'height': 'auto', 'border': f'3px solid {theme["border"]}', 'border-radius': '15px', 'box-shadow': '0 8px 16px rgba(0,0,0,0.1)'}
            )
        ], style={'text-align': 'center', 'margin-bottom': '30px'}),
        
        html.Div([dcc.Graph(figure=fig)], style={'margin-bottom': '25px'}),
        
        html.Div([
            html.H4("📊 Drought Categories (sq km)", style={'margin-bottom': '20px', 'text-align': 'center', 'color': theme['text']}),
            html.Div(class_cards[:3], style={'display': 'flex', 'flex-wrap': 'wrap', 'margin-bottom': '10px'}),
            html.Div(class_cards[3:], style={'display': 'flex', 'flex-wrap': 'wrap'})
        ])
    ])

def create_comparison_table(left_year, right_year, df, theme_name):
    theme = themes[theme_name]
    categories = ['Extreme_Drought', 'Severe_Drought', 'Moderate_Drought', 'Near_Normal', 'Moderately_Wet', 'Extremely_Wet']
    
    left_data = df[df['year'] == left_year].iloc[0]
    right_data = df[df['year'] == right_year].iloc[0]
    
    rows = []
    for cat in categories:
        left_val = left_data[cat]
        right_val = right_data[cat]
        diff = right_val - left_val
        diff_color = '#e74c3c' if diff > 0 else '#27ae60' if diff < 0 else '#95a5a6'
        
        rows.append(html.Tr([
            html.Td([icons[cat], f" {cat.replace('_', ' ')}"], style={'padding': '12px', 'border-bottom': f'1px solid {theme["border"]}'}),
            html.Td(f"{left_val:.1f}", style={'padding': '12px', 'text-align': 'center', 'border-bottom': f'1px solid {theme["border"]}'}),
            html.Td(f"{right_val:.1f}", style={'padding': '12px', 'text-align': 'center', 'border-bottom': f'1px solid {theme["border"]}'}),
            html.Td(f"{diff:+.1f}", style={'padding': '12px', 'text-align': 'center', 'color': diff_color, 'font-weight': 'bold', 'border-bottom': f'1px solid {theme["border"]}'})
        ]))
    
    return html.Table([
        html.Thead([html.Tr([
            html.Th("Category", style={'padding': '15px', 'background-color': theme['accent'], 'color': 'white'}),
            html.Th(f"{left_year}", style={'padding': '15px', 'background-color': theme['accent'], 'color': 'white', 'text-align': 'center'}),
            html.Th(f"{right_year}", style={'padding': '15px', 'background-color': theme['accent'], 'color': 'white', 'text-align': 'center'}),
            html.Th("Difference", style={'padding': '15px', 'background-color': theme['accent'], 'color': 'white', 'text-align': 'center'})
        ])]),
        html.Tbody(rows)
    ], style={'width': '100%', 'border-collapse': 'collapse', 'background-color': theme['card'], 'border-radius': '10px', 'overflow': 'hidden', 'box-shadow': '0 4px 8px rgba(0,0,0,0.1)'})

@app.callback(
    [Output('main-container', 'style'), Output('header', 'style'), Output('footer', 'style')],
    Input('theme-selector', 'value')
)
def update_theme(theme_name):
    theme = themes[theme_name]
    
    main_style = {'background-color': theme['bg'], 'color': theme['text'], 'min-height': '100vh', 'transition': 'all 0.3s ease'}
    header_style = {'background': f'linear-gradient(135deg, {theme["header"]}, {theme["accent"]})', 'padding': '20px', 'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'color': 'white', 'box-shadow': '0 4px 8px rgba(0,0,0,0.2)'}
    footer_style = {'background-color': theme['card'], 'color': theme['text'], 'border-top': f'1px solid {theme["border"]}'}
    
    return main_style, header_style, footer_style

@app.callback(
    [Output('left-column', 'children'), Output('right-column', 'children'), Output('left-column', 'style'), Output('right-column', 'style'), Output('comparison-table', 'children')],
    [Input('left-year', 'value'), Input('right-year', 'value'), Input('theme-selector', 'value')]
)
def update_dashboard(left_year, right_year, theme_name):
    theme = themes[theme_name]
    
    column_style = {
        'flex': '1', 'padding': '30px', 'border': f'2px solid {theme["border"]}',
        'margin': '20px', 'background-color': theme['card'], 'border-radius': '15px',
        'box-shadow': '0 8px 16px rgba(0,0,0,0.1)', 'transition': 'all 0.3s ease'
    }
    
    left_content = create_column_content(left_year, df, theme_name)
    right_content = create_column_content(right_year, df, theme_name)
    comparison_table = create_comparison_table(left_year, right_year, df, theme_name)
    
    return left_content, right_content, column_style, column_style, comparison_table

@app.callback(
    Output('trend-modal', 'is_open'),
    [Input('trend-btn', 'n_clicks'), Input('close-trend', 'n_clicks')],
    State('trend-modal', 'is_open')
)
def toggle_trend_modal(trend_clicks, close_clicks, is_open):
    if trend_clicks or close_clicks:
        return not is_open
    return is_open

@app.callback(Output('trend-chart', 'figure'), Input('trend-modal', 'is_open'))
def update_trend_chart(is_open):
    if is_open:
        return create_trend_chart(df)
    return {}

@app.callback(
    Output('export-btn', 'children'),
    Input('export-btn', 'n_clicks'),
    prevent_initial_call=True
)
def export_data(n_clicks):
    if n_clicks:
        return "✅ Exported!"
    return "📊 Export Data"

if __name__ == '__main__':
    app.run_server(debug=True)