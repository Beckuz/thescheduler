import React from "react";
import { Calendar, dateFnsLocalizer } from "react-big-calendar";
import format from "date-fns/format";
import parse from "date-fns/parse";
import startOfWeek from "date-fns/startOfWeek";
import getDay from "date-fns/getDay";
import "react-big-calendar/lib/css/react-big-calendar.css";
//import "react-big-calendar/lib/sass/styles";
import  data from "./default.json"

const locales = {
  "en-US": require("date-fns/locale/en-US")
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales
});

// This is where the events will go, it is best to make a seperate .json file which makes every class into an event
const myEventsList = [
  { start: new Date("2022-03-18T10:00:00"),
    end: new Date("2022-03-18T11:00:00"),
    title: "test2 event"}
];

let sessions = (data.sessions.map(({course, time, room, teacher}) => {
        return {
            title: course,
            start: new Date(time),
            end: new Date(time),
            room: room,
            teacher: teacher
        }
    }
))



  myEventsList.concat(
  )



export default function App() {
  return (
    <div className="App">
      <Calendar
        localizer={localizer}
        events={sessions}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 500 }}

      />
      

    </div>

  );
}