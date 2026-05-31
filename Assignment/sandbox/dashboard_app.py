from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge, Button, Card, CardContent, CardHeader, CardTitle,
    Checkbox, Column, H1, H2, H3, Muted, Progress, Ring, Row,
    Tab, Tabs, Text,
)
from prefab_ui.components.charts import (
    BarChart, ChartSeries, LineChart, PieChart, Sparkline,
)

with PrefabApp(css_class="max-w-5xl mx-auto p-6") as app:
    with Card():
        with CardHeader():
            CardTitle('Top 10 Highest Grossing Movies Analysis')
        with CardContent():
            with Tabs(value='overview'):
                with Tab('Overview', value='overview'):
                    with Column(gap=5):
                        with Column(gap=2):
                            H3('Top 10 Movies')
                            with Row(gap=3):
                                Text('Title')
                                Text('Gross ($)')
                            with Row(gap=3):
                                Text('Avatar')
                                Text('2.92B')
                            with Row(gap=3):
                                Text('Avengers: Endgame')
                                Text('2.80B')
                            with Row(gap=3):
                                Text('Avatar: The Way of Water')
                                Text('2.32B')
                            with Row(gap=3):
                                Text('Titanic')
                                Text('2.26B')
                            with Row(gap=3):
                                Text('Star Wars: TFA')
                                Text('2.07B')
                            with Row(gap=3):
                                Text('Avengers: Infinity War')
                                Text('2.05B')
                            with Row(gap=3):
                                Text('Spider-Man: NWH')
                                Text('1.92B')
                            with Row(gap=3):
                                Text('Jurassic World')
                                Text('1.67B')
                            with Row(gap=3):
                                Text('The Lion King')
                                Text('1.66B')
                            with Row(gap=3):
                                Text('The Avengers')
                                Text('1.52B')
                        with Column(gap=2):
                            H3('Gross Revenue by Movie')
                            BarChart(data=[{'x': 'Avatar', 'y': 2923706026}, {'x': 'Endgame', 'y': 2797501328}, {'x': 'Way of Water', 'y': 2320250281}, {'x': 'Titanic', 'y': 2257844554}, {'x': 'TFA', 'y': 2068223624}, {'x': 'Infinity War', 'y': 2048359754}, {'x': 'No Way Home', 'y': 1921847111}, {'x': 'Jurassic World', 'y': 1671537444}, {'x': 'Lion King', 'y': 1663075401}, {'x': 'The Avengers', 'y': 1518812988}],
                                     series=[ChartSeries(data_key='y', label='y')],
                                     x_axis='x', show_legend=False)
                with Tab('Frequent Actors', value='frequent_actors'):
                    with Column(gap=5):
                        with Column(gap=1):
                            H3('Actors appearing in > 2 movies')
                            Muted('Robert Downey Jr., Chris Evans, Mark Ruffalo, Chris Hemsworth, Scarlett Johansson (All appear in 3 movies).')
