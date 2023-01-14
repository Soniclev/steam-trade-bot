import React from 'react';
import { MenuItem, } from '@mui/material'
import { ListOutlined as ListItemIcon, ShoppingCart } from '@mui/icons-material'

import {
  Link
} from "react-router-dom";


export const mainListItems = (
  [
    (
      <MenuItem key="analyze-item" component={Link} to={'/analyze-item'}>
        <ListItemIcon>
          <ShoppingCart />
        </ListItemIcon>Analyze item
      </MenuItem>
    ),
    (
      <MenuItem key="view-items" component={Link} to={'/view-items'}>
        <ListItemIcon>
          <ShoppingCart />
        </ListItemIcon>View items
      </MenuItem>
    ),
    (
      <MenuItem key="second" component={Link} to={'/second'}>
        <ListItemIcon>
          <ShoppingCart />
        </ListItemIcon>Team 2
      </MenuItem>
    )
  ]
);
