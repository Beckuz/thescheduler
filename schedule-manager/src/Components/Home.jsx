import React, {useState} from "react";
import Schedule from "./Schedule";
import Login from "./Login/login";


function Home() {

    return (
        <div className="home">
            <div class="container">
                <Schedule />
            </div>
        </div>
    );
}

export default Home;
