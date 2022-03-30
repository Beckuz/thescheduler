import React, {useCallback, useState} from "react";
import {Calendar, dateFnsLocalizer, DateLocalizer} from "react-big-calendar";
import withDragAndDrop from 'react-big-calendar/lib/addons/dragAndDrop'
import format from "date-fns/format";
import parse from "date-fns/parse";
import startOfWeek from "date-fns/startOfWeek";
import getDay from "date-fns/getDay";
import "react-big-calendar/lib/css/react-big-calendar.css";
//import "react-big-calendar/lib/sass/styles";
import  data from "../default.json";
import {Dropdown} from "react-bootstrap";
import PropTypes from "prop-types";

const locales = {
  "en-US": require("date-fns/locale/en-US")
};
const DnDCalendar = withDragAndDrop(Calendar)

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales
});


export default function Schedule({}) {
    const [user, setUser] = useState("Admin");

    //Map sessions to list format for calendar
    let sessions = (data.sessions.map(({course,group, time,end, room, teacher},index) => {
                return {
                    id: index,
                    title: course,
                    start: new Date(time),
                    end: new Date(end),
                    room: room,
                    teacher: teacher,
                    group: group
                }
            }
        )
    )

    //Usestate for list so it can be updated
    const [myEvents, setMyEvents] = useState(sessions)


    //Callbacks to interact with the calendar
    const eventPropGetter = useCallback(
        (event) => ({
            ...(event.isDraggable
                ? { className: 'isDraggable' }
                : { className: 'nonDraggable' }),
        }),
        []
    )

    const moveEvent = useCallback(
        ({ event, start, end, isAllDay: droppedOnAllDaySlot = false }) => {
            const { allDay } = event
            if (!allDay && droppedOnAllDaySlot) {
                event.allDay = true
            }

            setMyEvents((prev) => {
                const existing = prev.find((ev) => ev.id === event.id) ?? {}
                const filtered = prev.filter((ev) => ev.id !== event.id)
                return [...filtered, { ...existing, start, end, allDay }]
            })
        },
        [setMyEvents]
    )

    const handleSelectSlot = useCallback(
        ({ start, end }) => {
            const title = window.prompt('New Event name')
            if (title) {
                setMyEvents((prev) => [...prev, { start, end, title }])
            }
        },
        [setMyEvents]
    )

    const resizeEvent = useCallback(
        ({ event, start, end }) => {
            setMyEvents((prev) => {
                const existing = prev.find((ev) => ev.id === event.id) ?? {}
                const filtered = prev.filter((ev) => ev.id !== event.id)
                return [...filtered, { ...existing, start, end }]
            })
        },
        [setMyEvents]
    )

    //Function to filter the events depending on the user
    function selectEvents(){
        if((user === "Admin")){
            return myEvents;
        }
        if (user === "NoviaYr1") {
            return myEvents.filter((event) =>
                event.group === user)
        }
        if(user === "EL"){
            return myEvents.filter((event) =>
                event.teacher === user);
        }
        if(user === "BL"){
            return myEvents.filter((event) =>
                event.teacher === user);
        }
    }



  return (
      <div>
          <Dropdown>
              <Dropdown.Toggle variant="secondary" id="dropdown-basic">
                  {user}
              </Dropdown.Toggle>

              <Dropdown.Menu>
                  <Dropdown.Item onClick={() => setUser("Admin")}>Admin</Dropdown.Item>
                  <Dropdown.Item onClick={() => setUser("EL")}>EL</Dropdown.Item>
                  <Dropdown.Item onClick={() => setUser("BL")}>BL</Dropdown.Item>
                  <Dropdown.Item onClick={() => setUser("NoviaYr1")}>Novia 1yr</Dropdown.Item>
              </Dropdown.Menu>
          </Dropdown>

        <div className="Schedule">
          <DnDCalendar
            localizer={localizer}
            events={selectEvents()}
            startAccessor="start"
            endAccessor="end"
            eventPropGetter={eventPropGetter}
            onEventDrop={moveEvent}
            onEventResize={resizeEvent}
            onSelectSlot={handleSelectSlot}
            popup
            rezisable
            style={{ height: 500 }}

          />
        </div>
      </div>
  );
}
Schedule.propTypes = {
    localizer: PropTypes.instanceOf(DateLocalizer),
}



