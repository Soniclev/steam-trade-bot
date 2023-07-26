import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import moment from "moment";

import ReactECharts from "echarts-for-react";

import { API_URL } from "../api";
import {
  formatPrice,
  formatPcs,
  formatTradableRestriction,
  formatMarketableRestriction,
  formatCommodity,
} from "./formats";

export default function MarketItem(props) {
  const [games, setGames] = useState([]);
  const [orders, setOrders] = useState([]);
  const [history, setHistory] = useState([]);

  const loadMeta = useCallback(() => {
    axios
      .get(
        `${API_URL}/get_market_item/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`
      )
      .then((response) => {
        setGames(response.data);
      });
  }, [props.app_id, props.market_hash_name]);

  useEffect(() => {
    loadMeta();
    axios
      .get(
        `${API_URL}/get_market_item_orders/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`
      )
      .then((response) => {
        setOrders(response.data);
      });
    axios
      .get(
        `${API_URL}/get_item_sell_history/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`
      )
      .then((response) => {
        console.log(response.data);
        setHistory(response.data);
      });
  }, [loadMeta, props.app_id, props.market_hash_name]);

  let option = {};
  if (history.history) {
    option = {
      tooltip: {
        trigger: "axis",
        position: function (pt) {
          return [pt[0], "10%"];
        },
      },
      title: {
        left: "left",
        text: "Price history",
      },
      toolbox: {
        feature: {
          dataZoom: {
            yAxisIndex: "none",
          },
          restore: {},
          saveAsImage: {},
        },
      },
      dataset: {
        dimensions: [
          "timestamp",
          "price",
          "price_no_fee",
          "price_game_fee",
          "price_steam_fee",
          "amount",
        ],
        source: history.history,
      },
      legend: {},
      xAxis: {
        type: "time",
        boundaryGap: false,
      },
      yAxis: [
        {
          type: "value",
          axisLabel: {
            // eslint-disable-next-line no-template-curly-in-string
            formatter: "${value}",
          },
          boundaryGap: [0, "100%"],
        },
        {
          type: "value",
          axisLabel: {
            formatter: "{value} pcs.",
          },
          boundaryGap: [0, "100%"],
        },
      ],
      dataZoom: [
        {
          type: "inside",
          start: 0,
          end: "100%",
        },
        {
          start: 0,
          end: "100%",
        },
      ],
      series: [
        {
          name: "Price",
          type: "line",
          symbol: "none",
          sampling: "average",
          itemStyle: {
            color: "rgb(0, 200, 0)",
          },
          encode: {
            x: "timestamp",
            y: "price",
          },
        },
        {
          name: "Amount",
          type: "line",
          symbol: "none",
          sampling: "average",
          yAxisIndex: 1,
          itemStyle: {
            color: "rgb(0, 70, 131)",
          },
          encode: {
            x: "timestamp",
            y: "amount",
          },
        },
      ],
    };
  }

  return (
    <div className="market-item-container">
      <h1>
        {props.app_id} - {props.market_hash_name}
      </h1>
      {history.history && (
        <>
          <ReactECharts option={option} style={{ height: 400 }} />
        </>
      )}
      <p>
        Marketable Restriction:{" "}
        {formatMarketableRestriction(games.market_marketable_restriction)}
      </p>
      <p>
        Tradable Restriction:{" "}
        {formatTradableRestriction(games.market_tradable_restriction)}
      </p>
      <p>
        Commodity: <i>{formatCommodity(games.commodity)}</i>
      </p>
      <h3>Orders</h3>
      <p>
        <i>Last orders update timestamp</i>:{" "}
        {moment(orders.timestamp).format("YYYY-MM-DD HH:mm:ssZ")}
      </p>
      <p>TODO: orders table</p>
      <h3>History</h3>
      <p>
        <i>Last history update timestamp</i>:{" "}
        {moment(history.timestamp).format("YYYY-MM-DD HH:mm:ssZ")}
      </p>
      <p>
        <i>First sale</i>:{" "}
        {moment(history.first_sale_datetime).format("YYYY-MM-DD HH:mm:ssZ")}
      </p>
      <p>
        <i>Last sale</i>:{" "}
        {moment(history.last_sale_datetime).format("YYYY-MM-DD HH:mm:ssZ")}
      </p>
      <p>
        <i>Total sold</i>: {formatPcs(history.total_sold)}
      </p>
      <p>
        <i>Total sold volume</i>: {formatPrice(history.total_volume)} (approx.{" "}
        {formatPrice(history.total_volume_approx_fee)} fees)
      </p>
    </div>
  );
}
