import * as React from 'react';
import PropTypes from 'prop-types';
import { Box, unstable_composeClasses } from '@mui/material';

import { ResponsiveLine } from '@nivo/line'

const static_data = [
    {
        "id": "Steam history",
        "color": "hsl(99, 70%, 50%)",
        "data": [
            { "x": "2022-07-29 01", "y": 4.279, "z": "16" },
            { "x": "2022-07-30 01", "y": 2.826, "z": "271" },
            { "x": "2022-07-31 01", "y": 1.547, "z": "179" }
        ]
    }
]


class AnalyzeItem extends React.Component {

    constructor(props) {
        super(props)
        this.state = {
            isLoaded: false,
            items: []
        };
    }

    componentDidMount() {
        fetch("http://127.0.0.1:8000/api/v1/get_item_sell_history/?app_id=730&market_hash_name=Sticker%20%7C%20Skull%20Lil%20Boney&currency=1")
            .then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        isLoaded: true,
                        items: [
                            {
                                "id": "Steam history",
                                "color": "hsl(99, 70%, 50%)",
                                "data": result.history.map(function (x) {
                                        return { "x": x[0].substring(0, 10), "y": x[1], "z": x[2] }
                                      })
                            }
                        ]
                    });
                    console.log(this.state);
                },
                // Note: it's important to handle errors here
                // instead of a catch() block so that we don't swallow
                // exceptions from actual bugs in components.
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            )
    }

    render() {
        return (
            <Box
                sx={{
                    height: 300
                }}
            >
                <ResponsiveLine
                    data={this.state.items}
                    margin={{ top: 50, right: 110, bottom: 50, left: 60 }}
                    xScale={{
                        type: 'time',
                        format: '%Y-%m-%d',
                        useUTC: false,
                        precision: 'day',
                    }}
                    yScale={{
                        type: 'linear',
                        min: 'auto',
                        max: 'auto',
                        stacked: true,
                        reverse: false
                    }}
                    xFormat="time:%Y-%m-%d %Hh"
                    yFormat=" >-.2f"
                    axisTop={null}
                    axisRight={null}
                    axisBottom={{
                        format: '%Y-%m-%d %Hh',
                        tickValues: 'every 1 days',
                        legend: 'Datetime',
                        legendOffset: 40,
                        legendPosition: 'middle'
                    }}
                    axisLeft={{
                        orient: 'left',
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: 0,
                        legend: 'Price',
                        legendOffset: -40,
                        legendPosition: 'middle'
                    }}
                    pointSize={10}
                    pointColor={{ theme: 'background' }}
                    pointBorderWidth={2}
                    pointBorderColor={{ from: 'serieColor' }}
                    pointLabelYOffset={-12}
                    useMesh={true}
                    enableSlices="x"
                    // TODO: check steam impl
                    sliceTooltip={({ slice }) => {
                        return (
                            <div
                                style={{
                                    background: 'white',
                                    padding: '9px 12px',
                                    border: '1px solid #ccc',
                                }}
                            >
                                {slice.points.map(point => (
                                    <div key={point.id}>Date: {point.data.x.toLocaleString()}
                                        <div
                                            style={{
                                                color: point.serieColor,
                                                padding: '3px 0',
                                            }}
                                        >
                                            <strong>Price:</strong> {point.data.y.toFixed(2)}<br />
                                            <strong>Sold:</strong> {point.data.z} items
                                        </div>
                                    </div>
                                ))}

                            </div>
                        )
                    }}
                    legends={[
                        {
                            anchor: 'bottom-right',
                            direction: 'column',
                            justify: false,
                            translateX: 100,
                            translateY: 0,
                            itemsSpacing: 0,
                            itemDirection: 'left-to-right',
                            itemWidth: 80,
                            itemHeight: 20,
                            itemOpacity: 0.75,
                            symbolSize: 12,
                            symbolShape: 'circle',
                            symbolBorderColor: 'rgba(0, 0, 0, .5)',
                            effects: [
                                {
                                    on: 'hover',
                                    style: {
                                        itemBackground: 'rgba(0, 0, 0, .03)',
                                        itemOpacity: 1
                                    }
                                }
                            ]
                        }
                    ]}
                />
            </Box >
        );
    }
}

AnalyzeItem.propTypes = {
        children: PropTypes.node,
    };

export default AnalyzeItem;
