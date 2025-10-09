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

# Configuration
USE_SQLITE = False

# Themes
themes = {
    'default': {'header': '#6A1B9A', 'bg': '#fafafa', 'card': '#ffffff', 'text': '#333333', 'border': '#e0e0e0', 'accent': '#8e24aa'},
    'dark': {'header': '#2d1b69', 'bg': '#121212', 'card': '#1e1e1e', 'text': '#ffffff', 'border': '#404040', 'accent': '#bb86fc'},
    'ocean': {'header': '#0077be', 'bg': '#f0f8ff', 'card': '#ffffff', 'text': '#333333', 'border': '#87ceeb', 'accent': '#4fc3f7'},
    'forest': {'header': '#228B22', 'bg': '#f5fff5', 'card': '#ffffff', 'text': '#333333', 'border': '#90ee90', 'accent': '#66bb6a'}
}

# Load data
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

# Add CSS animations
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
            @keyframes bounce { 0%, 20%, 50%, 80%, 100% {transform: translateY(0);} 40% {transform: translateY(-10px);} 60% {transform: translateY(-5px);} }
            @keyframes glow { 0%, 100% {box-shadow: 0 0 5px rgba(106, 27, 154, 0.5);} 50% {box-shadow: 0 0 20px rgba(106, 27, 154, 0.8);} }
            @keyframes rotate { from {transform: rotate(0deg);} to {transform: rotate(360deg);} }
            
            .fade-in { animation: fadeIn 0.6s ease-out; }
            .slide-in { animation: slideIn 0.5s ease-out; }
            .pulse { animation: pulse 2s infinite; }
            .bounce { animation: bounce 1s ease-in-out; }
            .glow { animation: glow 2s infinite; }
            .rotate { animation: rotate 2s linear infinite; }
            .hover-scale { transition: transform 0.3s ease, box-shadow 0.3s ease; }
            .hover-scale:hover { transform: scale(1.05); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
            
            @media (max-width: 768px) {
                .main-content { flex-direction: column !important; }
                .column { margin: 5px !important; padding: 15px !important; }
                .map-img { max-width: 100% !important; }
                .header-controls { flex-direction: column !important; gap: 10px; }
                #maps-container { flex-direction: column !important; }
            }
            
            .export-btn { background: linear-gradient(45deg, #6A1B9A, #8e24aa); color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; transition: all 0.3s; }
            .export-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(106, 27, 154, 0.3); }
            
            .trend-section { background: white; border-radius: 15px; padding: 20px; margin: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); }
            
            .Select-control { background-color: white !important; color: #333 !important; }
            .Select-menu-outer { background-color: white !important; }
            .Select-option { color: #333 !important; background-color: white !important; }
            .Select-option:hover { background-color: #f0f0f0 !important; color: #333 !important; }
            .Select-value-label { color: #333 !important; font-weight: bold !important; }
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

# Load data
df = load_data()
years = sorted(df['year'].unique())

# Color mapping
colors = {
    'Extreme_Drought': '#8B0000',
    'Severe_Drought': '#FF4500', 
    'Moderate_Drought': '#FFD700',
    'Near_Normal': '#32CD32',
    'Moderately_Wet': '#4169E1',
    'Extremely_Wet': '#0000FF'
}

# Icons mapping
icons = {
    'Extreme_Drought': '🔥',
    'Severe_Drought': '☀️',
    'Moderate_Drought': '🌤️',
    'Near_Normal': '🌱',
    'Moderately_Wet': '💧',
    'Extremely_Wet': '🌊'
}

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
        title="📈 Drought Categories Trend Over Time",
        xaxis_title="Year", yaxis_title="Area (sq km)",
        hovermode='x unified', height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# App layout
app.layout = html.Div(id='main-container', children=[
    dcc.Store(id='theme-store', data='default'),
    dcc.Store(id='show-trends', data=False),
    
    # Header
    html.Div(id='header', children=[
        html.H1("🌍Marathwada Drought Monitoring Dashboard", className='slide-in glow', style={'margin': '0', 'flex': '1'}),
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
                dcc.Dropdown(id='left-year', options=[{'label': year, 'value': year} for year in years], value=1984, style={'width': '100px', 'margin-right': '15px', 'color': '#333', 'backgroundColor': 'white', 'fontWeight': 'bold'})
            ]),
            html.Div([
                html.Label("Right Year:", style={'margin-right': '5px'}),
                dcc.Dropdown(id='right-year', options=[{'label': year, 'value': year} for year in years], value=1981, style={'width': '100px', 'margin-right': '15px', 'color': '#333', 'backgroundColor': 'white', 'fontWeight': 'bold'})
            ]),
            html.Button("📊💾 Export Data", id='export-btn', className='export-btn bounce'),
            html.Button("📈🔥 Show Trends", id='trend-btn', className='export-btn bounce', style={'margin-left': '10px'})
        ], style={'display': 'flex', 'align-items': 'center', 'flex-wrap': 'wrap', 'gap': '10px'})
    ]),
    
    # Trend Analysis Section
    html.Div(id='trend-section', className='trend-section fade-in', style={'display': 'none'}, children=[
        html.H3("📈🌊 Drought Trend Analysis 🕰️✨", className='glow', style={'text-align': 'center', 'margin-bottom': '20px'}),
        dcc.Graph(id='trend-chart')
    ]),
    
    # Maps Section
    html.Div(id='maps-section', className='fade-in', children=[
        html.H3("🗺️🌍 Maps Comparison 🔍", className='bounce', style={'text-align': 'center', 'margin': '30px 0 20px 0'}),
        html.Div(id='maps-container', style={'display': 'flex', 'justify-content': 'center', 'gap': '30px', 'flex-wrap': 'wrap', 'margin-bottom': '30px'})
    ]),
    
    # Pie Charts Section
    html.Div(id='pie-section', className='fade-in', children=[
        html.H3("📊🍰 Distribution Charts 📈✨", className='bounce', style={'text-align': 'center', 'margin': '30px 0 20px 0'}),
        html.Div(id='pie-container', style={'display': 'flex', 'justify-content': 'center', 'gap': '30px', 'flex-wrap': 'wrap', 'margin-bottom': '30px'})
    ]),
    
    # Classes Section
    html.Div(id='classes-section', className='fade-in', children=[
        html.H3("🎨🌡️ Drought Categories 📊🌊", className='bounce', style={'text-align': 'center', 'margin': '30px 0 20px 0'}),
        html.Div(id='classes-container', style={'display': 'flex', 'justify-content': 'center', 'gap': '30px', 'flex-wrap': 'wrap', 'margin-bottom': '30px'})
    ]),
    
    # Comparison Section
    html.Div(id='comparison-section', className='fade-in', children=[
        html.H3("📊🔄 Year Comparison Analysis 📈🔍", className='bounce', style={'text-align': 'center', 'margin': '30px 0 20px 0'}),
        html.Div(id='comparison-table')
    ]),
    
    # Footer
    html.Div(id='footer', children=[
        html.P([
            f"📅✨ Last Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')} | ",
            "💡🌍 Enhanced Drought Monitoring System 📊🔥"
        ], className='fade-in', style={'text-align': 'center', 'margin': '20px'})
    ])
])

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
            title=f"{year} Distribution", hole=0.3,
            color_discrete_map={cat.replace('_', ' '): colors[cat] for cat in pie_categories}
        )
        fig.update_traces(
            textinfo='percent', textfont_size=14,
            hovertemplate='<b>%{label}</b><br>Area: %{value:.1f} sq km<br>Percentage: %{percent}<extra></extra>'
        )
        fig.update_layout(
            showlegend=False, height=250, margin=dict(t=40, b=0, l=0, r=0),
            paper_bgcolor=theme['card'], plot_bgcolor=theme['card'], font_color=theme['text']
        )
    else:
        fig = px.pie(values=[1], names=['No Data'], title=f"{year} Distribution")
    
    # Create class cards in horizontal layout
    class_cards = []
    for cat in categories:
        value = year_data[cat]
        
        class_cards.append(
            html.Div([
                html.Div([
                    html.Span(icons[cat], style={'font-size': '18px', 'margin-right': '5px'}),
                    html.Span(cat.replace('_', ' '), style={'font-weight': 'bold', 'font-size': '10px', 'color': 'white'})
                ], style={'text-align': 'center', 'padding': '6px'}),
                html.Div(f"{value:.1f}", style={
                    'text-align': 'center', 'font-weight': 'bold', 'font-size': '12px',
                    'color': 'white', 'padding': '4px'
                })
            ], style={
                'background-color': colors[cat],
                'border-radius': '6px',
                'margin': '2px',
                'flex': '1',
                'min-width': '140px',
                'height': '100px'

            })
        )
    
    return html.Div([
        # Map section at top
        html.Div([
            html.H4(f"{year} Year", style={'text-align': 'center', 'margin-bottom': '10px', 'color': theme['text']}),
            html.Img(
                src=get_map_image(year_data['Map Images Left']),
                style={'width': '100%', 'max-width': '400px', 'height': 'auto', 'border': '2px solid #ddd', 'border-radius': '8px'}
            )
        ], style={'text-align': 'center', 'margin-bottom': '20px'}),
        
        # Pie chart in middle
        html.Div([dcc.Graph(figure=fig)], style={'margin-bottom': '20px'}),
        
        # Classes at bottom in horizontal layout
        html.Div([
            html.Div(class_cards[:3], style={'display': 'flex', 'margin-bottom': '3px'}),
            html.Div(class_cards[3:], style={'display': 'flex'})
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
    ], style={'width': '100%', 'border-collapse': 'collapse', 'background-color': theme['card'], 'border-radius': '10px', 'overflow': 'hidden', 'box-shadow': '0 4px 8px rgba(0,0,0,0.1)', 'margin': '0 20px'})

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



def create_maps_section(left_year, right_year, df, theme_name):
    theme = themes[theme_name]
    left_data = df[df['year'] == left_year].iloc[0]
    right_data = df[df['year'] == right_year].iloc[0]
    
    return html.Div([
        html.Div([
            html.H4(f"📅 {left_year} Year", style={'text-align': 'center', 'margin-bottom': '15px', 'color': theme['text']}),
            html.Img(
                src=get_map_image(left_data['Map Images Left']),
                className='fade-in pulse hover-scale',
                style={'width': '100%', 'max-width': '400px', 'height': 'auto', 'border': '2px solid #ddd', 'border-radius': '8px'}
            )
        ], style={'text-align': 'center', 'flex': '1', 'margin': '0 15px'}),
        
        html.Div([
            html.H4(f"📅 {right_year} Year", style={'text-align': 'center', 'margin-bottom': '15px', 'color': theme['text']}),
            html.Img(
                src=get_map_image(right_data['Map Images Left']),
                className='fade-in pulse hover-scale',
                style={'width': '100%', 'max-width': '400px', 'height': 'auto', 'border': '2px solid #ddd', 'border-radius': '8px'}
            )
        ], style={'text-align': 'center', 'flex': '1', 'margin': '0 15px'})
    ], style={'display': 'flex', 'justify-content': 'center', 'gap': '20px', 'flex-wrap': 'wrap'})

def create_pie_charts_section(left_year, right_year, df, theme_name):
    theme = themes[theme_name]
    
    def create_pie_chart(year):
        year_data = df[df['year'] == year].iloc[0]
        categories = ['Extreme_Drought', 'Severe_Drought', 'Moderate_Drought', 'Near_Normal', 'Moderately_Wet', 'Extremely_Wet']
        values = [year_data[cat] for cat in categories]
        non_zero_data = [(cat, val) for cat, val in zip(categories, values) if val > 0]
        
        if non_zero_data:
            pie_categories, pie_values = zip(*non_zero_data)
            fig = px.pie(
                values=pie_values, names=[cat.replace('_', ' ') for cat in pie_categories],
                title=f"{year} Distribution", hole=0.3,
                color_discrete_map={cat.replace('_', ' '): colors[cat] for cat in pie_categories}
            )
            fig.update_traces(
                textinfo='percent', textfont_size=14,
                hovertemplate='<b>%{label}</b><br>Area: %{value:.1f} sq km<br>Percentage: %{percent}<extra></extra>'
            )
            fig.update_layout(
                showlegend=False, height=300, margin=dict(t=40, b=0, l=0, r=0),
                paper_bgcolor=theme['card'], plot_bgcolor=theme['card'], font_color=theme['text']
            )
        else:
            fig = px.pie(values=[1], names=['No Data'], title=f"{year} Distribution")
        return fig
    
    return html.Div([
        html.Div([dcc.Graph(figure=create_pie_chart(left_year))], style={'flex': '1', 'margin': '0 15px'}),
        html.Div([dcc.Graph(figure=create_pie_chart(right_year))], style={'flex': '1', 'margin': '0 15px'})
    ], style={'display': 'flex', 'justify-content': 'center', 'gap': '20px', 'flex-wrap': 'wrap'})

def create_classes_section(left_year, right_year, df, theme_name):
    def create_class_cards(year):
        year_data = df[df['year'] == year].iloc[0]
        categories = ['Extreme_Drought', 'Severe_Drought', 'Moderate_Drought', 'Near_Normal', 'Moderately_Wet', 'Extremely_Wet']
        class_cards = []
        
        for cat in categories:
            value = year_data[cat]
            class_cards.append(
                html.Div([
                    html.Div([
                        html.Span(icons[cat], style={'font-size': '18px', 'margin-right': '5px'}),
                        html.Span(cat.replace('_', ' '), style={'font-weight': 'bold', 'font-size': '10px', 'color': 'white'})
                    ], style={'text-align': 'center', 'padding': '6px'}),
                    html.Div(f"{value:.1f}", style={
                        'text-align': 'center', 'font-weight': 'bold', 'font-size': '12px',
                        'color': 'white', 'padding': '4px'
                    })
                ], className='hover-scale', style={
                    'background-color': colors[cat],
                    'border-radius': '6px',
                    'margin': '2px',
                    'flex': '1',
                    'min-width': '140px',
                    'height': '80px',
                    'cursor': 'pointer',
                    'transition': 'all 0.4s ease'
                })
            )
        
        return html.Div([
            html.Div(class_cards[:3], style={'display': 'flex', 'margin-bottom': '8px', 'justify-content': 'center'}),
            html.Div(class_cards[3:], style={'display': 'flex', 'justify-content': 'center'})
        ], style={'width': '100%', 'max-width': '500px'})
    
    return html.Div([
        html.Div([create_class_cards(left_year)], style={'flex': '1', 'margin': '0 15px'}),
        html.Div([create_class_cards(right_year)], style={'flex': '1', 'margin': '0 15px'})
    ], style={'display': 'flex', 'justify-content': 'center', 'gap': '20px', 'flex-wrap': 'wrap'})

@app.callback(
    [Output('maps-container', 'children'), Output('pie-container', 'children'), 
     Output('classes-container', 'children'), Output('comparison-table', 'children')],
    [Input('left-year', 'value'), Input('right-year', 'value'), Input('theme-selector', 'value')]
)
def update_dashboard(left_year, right_year, theme_name):
    maps_section = create_maps_section(left_year, right_year, df, theme_name)
    pie_section = create_pie_charts_section(left_year, right_year, df, theme_name)
    classes_section = create_classes_section(left_year, right_year, df, theme_name)
    comparison_table = create_comparison_table(left_year, right_year, df, theme_name)
    
    return maps_section, pie_section, classes_section, comparison_table

@app.callback(
    [Output('trend-section', 'style'), Output('trend-chart', 'figure')],
    Input('trend-btn', 'n_clicks')
)
def toggle_trends(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        return {'display': 'block'}, create_trend_chart(df)
    return {'display': 'none'}, {}

@app.callback(
    Output('export-btn', 'children'),
    Input('export-btn', 'n_clicks'),
    prevent_initial_call=True
)
def export_data(n_clicks):
    if n_clicks:
        return "✅ Exported!"
    return "📊 Export"
# Expose server for Render
server = app.server
if __name__ == "__main__":
    # Bind to 0.0.0.0 and use PORT from environment for Render
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)