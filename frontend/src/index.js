import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";

import {
  createBrowserRouter,
  RouterProvider,
  useParams,
} from "react-router-dom";
import Root from "./routes/root";
import Apps from "./routes/apps";
import AppMarketItems from "./routes/app_market_items";
import MarketItem from "./routes/market_item";
import EntireMarketDailyStats from './routes/entire_market_stats';

const root = ReactDOM.createRoot(document.getElementById("root"));

const AppMarketItemsWrapper = () => {
  const { app_id } = useParams();
  return <AppMarketItems app_id={app_id} />;
};

const MarketItemWrapper = () => {
  const { app_id, market_hash_name } = useParams();
  console.log("MarketItemWrapper");
  return <MarketItem app_id={app_id} market_hash_name={market_hash_name} />;
};

const router = createBrowserRouter([
  {
    path: "/",
    element: <Root />,
    children: [
      {
        path: "/",
        element: <App />,
      },
      {
        path: "apps",
        element: <Apps />,
      },
      {
        path: "entire_market_daily_stats",
        element: <EntireMarketDailyStats />,
      },
      {
        path: "apps/:app_id",
        element: <AppMarketItemsWrapper />,
      },
      {
        path: "apps/:app_id/:market_hash_name",
        element: <MarketItemWrapper />,
      },
    ],
  },
]);

root.render(
  <React.StrictMode>
    {/* <App /> */}
    <RouterProvider router={router} />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
