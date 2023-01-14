import * as React from 'react';
import PropTypes from 'prop-types';
import Typography from '@mui/material/Typography';

function LeftBar(props) {
  return (
    <Typography component="h2" variant="h6" color="primary" gutterBottom>
      Text123
    </Typography>
  );
}

LeftBar.propTypes = {
  children: PropTypes.node,
};

export default LeftBar;