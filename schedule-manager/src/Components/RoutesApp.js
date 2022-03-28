import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import {About, Footer, Home, Navigation} from "./index";
import React from "react";
import Login from "./Login/login";
import PropTypes from "prop-types";
import useToken from './Login/useToken';

function RoutesApp(){
    const { token, setToken } = useToken();

    if(!token) {
        return <Login setToken={setToken} />
    }
    return(
            <Router>
                <Navigation />
                <Routes>
                    <Route exact path="/login" element={<Login/>}/>
                    <Route path="/" element={<Home />} />
                    <Route path="/about" element={<About />} />
                </Routes>
                <Footer />
            </Router>
        );

}

export default RoutesApp;
Login.propTypes = {
    setToken: PropTypes.func.isRequired
}