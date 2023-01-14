import React from 'react';
import {
  Routes,
  Route,
} from "react-router-dom";
import AnalyzeItem from './components/AnalyzeItem';
import LeftBar from './components/LeftBar';
import LeftBar2 from './components/LeftBar2';


var routes = (
  <Routes>
    <Route path="/analyze-item" element={<AnalyzeItem />} />
    <Route path="/view-items" element={<LeftBar />} />
    <Route path="/second" element={<LeftBar2 />} />
  </Routes>
);


export default routes;

