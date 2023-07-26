import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";

import {API_URL} from "../api";


export default function Apps() {
  const [games, setGames] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL}/get_games/?count=100&offset=0`).then((response) => {
      setGames(response.data.items);
    });
  }, []);

  const columnHelper = createColumnHelper();

  const columns = React.useMemo(
    () => [
      columnHelper.accessor((row) => row.app_id, {
        id: "app_id",
        cell: (info) => info.getValue(),
        header: () => <span>App ID</span>,
      }),
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (info) => <i>{info.getValue()}</i>,
        header: () => <span>Name</span>,
      }),
    ],
    [columnHelper]
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
    <div className="game-container">
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
                  <Link to={`/apps/${row.getValue("app_id")}`}>View</Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
