import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from 'react-router-dom';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";

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


export default function AppMarketItems(props) {
  const [games, setGames] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL}/get_market_items/?app_id=${props.app_id}&count=100&offset=0`).then((response) => {
      setGames(response.data.items);
    });
  }, [props.app_id]);

  const columnHelper = createColumnHelper();

  const columns = React.useMemo(
    () => [
      columnHelper.accessor((row) => row.market_hash_name, {
        id: "market_hash_name",
        cell: (info) => info.getValue(),
        header: () => <span>Market Hash Name</span>,
      }),
      columnHelper.accessor((row) => row.market_marketable_restriction, {
        id: "market_marketable_restriction",
        cell: (info) => formatMarketableRestriction(info.getValue()),
        header: () => <span>Marketable Restriction</span>,
      }),
      columnHelper.accessor((row) => row.market_tradable_restriction, {
        id: "market_tradable_restriction",
        cell: (info) => formatTradableRestriction(info.getValue()),
        header: () => <span>Tradable Restriction</span>,
      }),
      columnHelper.accessor((row) => row.commodity, {
        id: "commodity",
        cell: (info) => <i>{formatCommodity(info.getValue())}</i>,
        header: () => <span>Commodity</span>,
      }),
    ],
    []
  );

  const data = React.useMemo(() => games, [games]);

  const table = useReactTable({
    data,
    columns,
    // Pipeline
    getCoreRowModel: getCoreRowModel(),
    debugTable: true,
  });

  return (
    <div className="market-items-container">
      <h1>App ID is {props.app_id}</h1>
      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((column) => (
                <th key={column.id}>
                  {column.isPlaceholder
                    ? null
                    : flexRender(
                        column.column.columnDef.header,
                        column.getContext()
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => {
            // prepareRow(row);
            return (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => {
                  return (
                    <td key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  );
                })}
                <td>
                  <Link to={`/apps/${props.app_id}/${row.getValue("market_hash_name")}`}>View</Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
