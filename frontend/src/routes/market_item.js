import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import moment from 'moment';


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


export default function MarketItem(props) {
  const [games, setGames] = useState([]);
  const [orders, setOrders] = useState([]);
  const [history, setHistory] = useState([]);

  const loadMeta = useCallback(() => {
    axios.get(`${API_URL}/get_market_item/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`).then((response) => {
      setGames(response.data);
    });
  })

  useEffect(() => {
    console.log('useEffect called');
    loadMeta();
    axios.get(`${API_URL}/get_market_item_orders/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`).then((response) => {
      setOrders(response.data);
    });
    axios.get(`${API_URL}/get_item_sell_history/?app_id=${props.app_id}&market_hash_name=${props.market_hash_name}`).then((response) => {
      setHistory(response.data);
    });
  }, [props.app_id, props.market_hash_name]);

  // const data = React.useMemo(() => games, [games]);
  // const ordersData = React.useMemo(() => orders, [orders]);
  // const historyData = React.useMemo(() => history, [history]);

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
    </div>
  );
}
