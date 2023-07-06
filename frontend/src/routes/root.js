import { Outlet, Link } from "react-router-dom";

export default function Root() {
    return (
      <>
        <div id="sidebar">
          <h1>Steam Market Tools</h1>
          <nav>
            <ul>
              <li>
              <Link to={``}>Main App</Link>
              </li>
              <li>
              <Link to={`apps`}>Market items</Link>
              </li>
            </ul>
          </nav>
        </div>
        <div id="detail">
            <Outlet />
        </div>
      </>
    );
  }
