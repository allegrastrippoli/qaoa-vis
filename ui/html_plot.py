import json

def create_init_html():
    return f"""
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <div id="plot" style="width:100%;height:100%"></div>
        <script>
            Plotly.newPlot('plot', [], {{
                title: 'QAOA',
                xaxis: {{ title: '', type: 'category' }},
                yaxis: {{ title: '' }}
            }});
        </script>
    </body>
    </html>
    """


def create_plot_html(states, data, params, y_range, num_runs, title):
    traces_js = ""
    for (key, y_list) in data.items():
        for  i, y_vals in enumerate(y_list):
            x_val = states         
            y_val = y_vals          
            param_label = params[i%num_runs]
            traces_js += f"""
            {{
                x: {x_val},
                y: {y_val},
                mode: 'lines+markers',
                name: 'γ,β={param_label}'
            }},"""
        break

    html = f"""
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <div id="plot" style="width:100%; height:100%;"></div>

        <script>
            var traces = [{traces_js}];

            var layout = {{
                title: "{title}",
                xaxis: {{
                    title: "State",
                    type: "category"
                }},
                yaxis: {{
                    title: "Value",
                    range: [{y_range[0]}, {y_range[1]}]
                }}
            }};

            Plotly.newPlot("plot", traces, layout);

            // Keep track of visibility for animation
            var traceVisibility = traces.map(() => true);

            var plotElement = document.getElementById("plot");

            plotElement.on("plotly_legendclick", function(eventData) {{
                var traceIndex = eventData.curveNumber;
                traceVisibility[traceIndex] = !traceVisibility[traceIndex];
            }});

            plotElement.on("plotly_legenddoubleclick", function(eventData) {{
                return false;
            }});

            // Update Y-values dynamically
            function updateData(newYs) {{
                for (var i = 0; i < newYs.length; i++) {{
                    if (traceVisibility[i]) {{
                        Plotly.animate("plot", {{
                            data: [{{ y: newYs[i], visible: true }}],
                            traces: [i],
                        }}, {{
                            transition: {{ duration: 0 }},
                            frame: {{ duration: 100, redraw: false }}
                        }});
                    }} else {{
                        Plotly.restyle("plot", {{ visible: "legendonly" }}, [i]);
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html


def build_visjs_html(edges):
    nodes = sorted(set([n for e in edges for n in e]))

    js_nodes = json.dumps([{"id": n, "label": str(n)} for n in nodes])
    js_edges = json.dumps([{"from": u, "to": v} for u, v in edges])

    return f"""
    <html>
    <head>
        <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style>#graph {{ width:100%; height:100vh; }}</style>
    </head>
    <body>
        <div id="graph"></div>
        <script>
            var nodes = new vis.DataSet({js_nodes});
            var edges = new vis.DataSet({js_edges});

            var network = new vis.Network(
                document.getElementById('graph'),
                {{nodes:nodes, edges:edges}},
                {{
                    physics:true,
                    nodes:{{shape:'dot', size:10}},
                    edges:{{smooth:{{type:'continuous'}}}}
                }}
            );
        </script>
    </body>
    </html>
    """
