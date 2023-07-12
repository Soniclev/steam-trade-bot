import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import moment from 'moment';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';


ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);


const API_URL =
  process.env.NODE_ENV === "production"
    ? "https://example.com/api/v1"
    : "http://localhost:8000/api/v1";

function formatTradableRestriction(value) {
  if (value === -1)
    return "🚫Not tradable (Sell only) ";
  if (value === null)
    return "✅No"
  return `🔒${value} days`
}

function formatMarketableRestriction(value) {
  if (value === null || value === 0)
    return "✅No"
  return `🔒${value} days`
}


function formatCommodity(value) {
  return value ? "Yes" : "No"
}


function formatPrice(value, currency=1) {
  if (value)
    return `$${value.toLocaleString()}`;
  return null;
}


function formatPcs(value) {
  if (value)
    return value.toLocaleString() + " pcs.";
  return null;
}


export const options = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Chart.js Line Chart',
    },
  },
};

const labels = [1, 2, 3];
const data = {
  labels,
  datasets: [
    {
      label: 'Dataset 1',
      data: [4, 5, 6],
      borderColor: 'rgb(255, 99, 132)',
      backgroundColor: 'rgba(255, 99, 132, 0.5)',
    },
  ]
};


export default function MarketItem(props) {
  const [games, setGames] = useState([]);
  const [orders, setOrders] = useState([]);
  const [history, setHistory] = useState([]);

  const loadMeta = useCallback(() => {
    axios.get(`${API_URL}/get_market_item/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`).then((response) => {
      setGames(response.data);
    });
  }, [props.app_id, props.market_hash_name])

  useEffect(() => {
    console.log('useEffect called');
    loadMeta();
    axios.get(`${API_URL}/get_market_item_orders/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`).then((response) => {
      
      setOrders(response.data);
    });
    axios.get(`${API_URL}/get_item_sell_history/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`).then((response) => {
      console.log(response.data);
      setHistory(response.data);
    });
  }, [loadMeta, props.app_id, props.market_hash_name]);

  if (history.history)
    console.log(history["history"].map((x) => x[1]))

  return (
    <div className="market-item-container">
      <h1>{props.app_id} - {props.market_hash_name}</h1>
      <p>Marketable Restriction: {formatMarketableRestriction(games.market_marketable_restriction)}</p>
      <p>Tradable Restriction: {formatTradableRestriction(games.market_tradable_restriction)}</p>
      <p>Commodity: <i>{formatCommodity(games.commodity)}</i></p>
      <h3>Orders</h3>
      <p><i>Last orders update timestamp</i>: {moment(orders.timestamp).format('YYYY-MM-DD HH:mm:ssZ')}</p>
      <p>TODO: orders table</p>
      <h3>History</h3>
      <p><i>Last history update timestamp</i>: {moment(history.timestamp).format('YYYY-MM-DD HH:mm:ssZ')}</p>
      <p><i>First sale</i>: {moment(history.first_sale_datetime).format('YYYY-MM-DD HH:mm:ssZ')}</p>
      <p><i>Last sale</i>: {moment(history.last_sale_datetime).format('YYYY-MM-DD HH:mm:ssZ')}</p>
      <p><i>Total sold</i>: {formatPcs(history.total_sold)}</p>
      <p><i>Total sold volume</i>: {formatPrice(history.total_volume)} (approx. {formatPrice(history.total_volume_approx_fee)} fees)</p>
      {history.history && <Line options={options} data={{
  labels: history.history.map((x) => x[0]),
  datasets: [
    {
      label: 'Dataset 1',
      data: history.history.map((x) => x[1]),
      borderColor: 'rgb(255, 99, 132)',
      backgroundColor: 'rgba(255, 99, 132, 0.5)',
    },
  ]
}} />
        }
    </div>
  );
}
