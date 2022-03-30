import {Dropdown} from "react-bootstrap";
import React, {useState} from "react";

export default function UserSelect (){
    const [user, setUser] = useState("Choose User");


    return(
        <Dropdown>
            <Dropdown.Toggle variant="secondary" id="dropdown-basic">
                {user}
            </Dropdown.Toggle>

            <Dropdown.Menu>
                <Dropdown.Item onClick={() => setUser("Admin")}>Admin</Dropdown.Item>
                <Dropdown.Item onClick={() => setUser("EL")}>EL</Dropdown.Item>
                <Dropdown.Item onClick={() => setUser("BL")}>BL</Dropdown.Item>
                <Dropdown.Item onClick={() => setUser("Novia 1yr")}>Novia 1yr</Dropdown.Item>
            </Dropdown.Menu>
        </Dropdown>
    );
}
