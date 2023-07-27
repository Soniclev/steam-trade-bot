import React, { useState, useEffect } from "react";
import axios from "axios";
import moment from "moment";
import ReactECharts from "echarts-for-react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
} from "@tanstack/react-table";
import { API_URL } from "../api";
import { formatPrice, formatPcs } from "./formats";

export default function EntireMarketStats(props) {
  const [stats, setStats] = useState([]);
  const [selectedMode, setSelectedMode] = useState("monthly");

  useEffect(() => {
    axios
      .get(`${API_URL}/get_entire_market_stats/?mode=${selectedMode}`)
      .then((response) => {
        setStats(response.data);
      });
  }, [selectedMode]);

  const handleModeChange = (mode) => {
    setSelectedMode(mode);
  };

  const columnHelper = createColumnHelper();

  const columns = React.useMemo(
    () => [
      columnHelper.accessor((row) => row.point_timestamp, {
        id: "point_timestamp",
        cell: (info) => moment(info.getValue()).format("DD.MM.YYYY"),
        header: () => <span>Date</span>,
      }),
      columnHelper.accessor((row) => row.avg_price, {
        id: "avg_price",
        cell: (info) => formatPrice(info.getValue()),
        header: () => <span>Average Price</span>,
      }),
      columnHelper.accessor((row) => row.volume, {
        id: "volume",
        cell: (info) => formatPrice(info.getValue()),
        header: () => <span>Volume</span>,
      }),
      columnHelper.accessor((row) => row.quantity, {
        id: "quantity",
        cell: (info) => formatPcs(info.getValue()),
        header: () => <span>Sold quantity</span>,
      }),
      columnHelper.accessor((row) => row.sold_unique_items, {
        id: "sold_unique_items",
        cell: (info) => info.getValue(),
        header: () => <span>Sold unique items</span>,
      }),
    ],
    [columnHelper]
  );

  const data = React.useMemo(() => stats, [stats]);

  const table = useReactTable({
    data,
    columns,
    // Pipeline
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    debugTable: true,
  });

  let option = {
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
        "point_timestamp",
        "avg_price",
        "volume",
        "volume_no_fee",
        "volume_game_fee",
        "volume_steam_fee",
        "quantity",
        "sold_unique_items",
      ],
      source: data,
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
        name: "Volume",
        type: "line",
        symbol: "none",
        sampling: "average",
        itemStyle: {
          color: "rgb(0, 200, 0)",
        },
        encode: {
          x: "point_timestamp",
          y: "volume",
        },
      },
      {
        name: "Average price",
        type: "line",
        symbol: "none",
        sampling: "average",
        itemStyle: {
          color: "rgb(200, 0, 0)",
        },
        encode: {
          x: "point_timestamp",
          y: "avg_price",
        },
      },
      {
        name: "Sold items",
        type: "line",
        symbol: "none",
        sampling: "average",
        yAxisIndex: 1,
        itemStyle: {
          color: "rgb(200, 200, 0)",
        },
        encode: {
          x: "point_timestamp",
          y: "quantity",
        },
      },
      {
        name: "Sold unique items",
        type: "line",
        symbol: "none",
        sampling: "average",
        yAxisIndex: 1,
        itemStyle: {
          color: "rgb(200, 200, 200)",
        },
        encode: {
          x: "point_timestamp",
          y: "sold_unique_items",
        },
      },
    ],
  };

  return (
    <div className="market-items-container">
      <h1>Global market {selectedMode} stats</h1>
      <div>
        <h2>Selected Mode: {selectedMode}</h2>
        <button onClick={() => handleModeChange("monthly")}>Monthly</button>
        <button onClick={() => handleModeChange("weekly")}>Weekly</button>
        <button onClick={() => handleModeChange("daily")}>Daily</button>
      </div>
      <div style={{ width: "1000px", height: "500px" }}>
        <ReactECharts option={option} style={{ height: 500 }} />
      </div>

      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                return (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder ? null : (
                      <div>
                        <div
                          {...{
                            className: header.column.getCanSort()
                              ? "cursor-pointer select-none"
                              : "",
                            onClick: header.column.getToggleSortingHandler(),
                          }}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                          {{
                            asc: " 🔼",
                            desc: " 🔽",
                          }[header.column.getIsSorted()] ?? null}
                        </div>
                        {header.column.getCanFilter() ? (
                          <div>
                            <Filter column={header.column} table={table} />
                          </div>
                        ) : null}
                      </div>
                    )}
                  </th>
                );
              })}
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
              </tr>
            );
          })}
        </tbody>
        <div className="h-2" />
        <div className="flex items-center gap-2">
          <button
            className="border rounded p-1"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            {"<<"}
          </button>
          <button
            className="border rounded p-1"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            {"<"}
          </button>
          <button
            className="border rounded p-1"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            {">"}
          </button>
          <button
            className="border rounded p-1"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          >
            {">>"}
          </button>
          <span className="flex items-center gap-1">
            <div>Page</div>
            <strong>
              {table.getState().pagination.pageIndex + 1} of{" "}
              {table.getPageCount()}
            </strong>
          </span>
          <span className="flex items-center gap-1">
            | Go to page:
            <input
              type="number"
              defaultValue={table.getState().pagination.pageIndex + 1}
              onChange={(e) => {
                const page = e.target.value ? Number(e.target.value) - 1 : 0;
                table.setPageIndex(page);
              }}
              className="border p-1 rounded w-16"
            />
          </span>
          <select
            value={table.getState().pagination.pageSize}
            onChange={(e) => {
              table.setPageSize(Number(e.target.value));
            }}
          >
            {[10, 20, 30, 40, 50].map((pageSize) => (
              <option key={pageSize} value={pageSize}>
                Show {pageSize}
              </option>
            ))}
          </select>
        </div>
        <div>{table.getRowModel().rows.length} Rows</div>
        <pre>{JSON.stringify(table.getState().pagination, null, 2)}</pre>
        <pre>{JSON.stringify(table.getState().sorting, null, 2)}</pre>
      </table>
    </div>
  );
}

function Filter({ column, table }) {
  const firstValue = table
    .getPreFilteredRowModel()
    .flatRows[0]?.getValue(column.id);

  const columnFilterValue = column.getFilterValue();

  return typeof firstValue === "number" ? (
    <div className="flex space-x-2">
      <input
        type="number"
        value={columnFilterValue?.[0] ?? ""}
        onChange={(e) =>
          column.setFilterValue((old) => [e.target.value, old?.[1]])
        }
        placeholder={`Min`}
        className="w-24 border shadow rounded"
      />
      <input
        type="number"
        value={columnFilterValue?.[1] ?? ""}
        onChange={(e) =>
          column.setFilterValue((old) => [old?.[0], e.target.value])
        }
        placeholder={`Max`}
        className="w-24 border shadow rounded"
      />
    </div>
  ) : (
    <input
      type="text"
      value={columnFilterValue ?? ""}
      onChange={(e) => column.setFilterValue(e.target.value)}
      placeholder={`Search...`}
      className="w-36 border shadow rounded"
    />
  );
}
