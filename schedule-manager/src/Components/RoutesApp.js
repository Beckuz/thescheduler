import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import {About, Footer, Home, Navigation} from "./index";
import React from "react";
import Login from "./Login/login";

function RoutesApp(){
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