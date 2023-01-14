import * as React from 'react';
import PropTypes from 'prop-types';
import Typography from '@mui/material/Typography';

function LeftBar2(props) {
  return (
    <Typography component="h2" variant="h6" color="primary" gutterBottom>
      ZXC
    </Typography>
  );
}

LeftBar2.propTypes = {
  children: PropTypes.node,
};

export default LeftBar2;