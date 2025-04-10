//geeks for geeks js code template was used here, though much has been added to it since then
//https://www.geeksforgeeks.org/how-to-design-a-simple-calendar-using-javascript/

let event_data;
let event_json;

let assignment_data;
let assignment_json;

let assignment_data_temp;
let assignment_json_temp;

let events;
let user_events_json;


//Global variable to store current day being viewed in modal
var modal_day = -1;


//the fetch below gets the data from study_event and study_time and puts it into json format


async function getAssignments() {
    console.log("test");
    await fetch('/canvas/assignments')
        .then(response => response.json())
        .then(data => {
            // Parses the data, making it usable
            assignment_data = "[" + String(data) + "]";
            assignment_data = assignment_data.replaceAll("'", '"');
            assignment_json = JSON.parse(assignment_data);

            //console.log(assignment_data);


        })
        .catch(error => {
            console.error('Error:', error);
        });
    

}
waitOnAssignments();

async function waitOnAssignments() {

    await getAssignments();
    manipulate();
    await refreshAssignments();
    manipulate();
}


async function refreshAssignments() {
    console.log("test");
    await fetch('/canvas/assignments/refresh')
        .then(response => response.json())
        .then(data => {
            // Parses the data, making it usable
            assignment_data_temp = "[" + String(data) + "]";
            assignment_data_temp = assignment_data.replaceAll("'", '"');
            assignment_json_temp = JSON.parse(assignment_data);

            //console.log(assignment_data_temp);


        })
        .catch(error => {
            console.error('Error:', error);
        });
    assignment_data = assignment_data_temp;
    assignment_json = assignment_json_temp;
    getAssignments();

}



//Gets scheduled events from db
async function getEvents() {
    await fetch('/api/event_times')
        .then(response => response.json())
        .then(data => {
            // Parses the data, making it usable
            event_data = "[" + String(data) + "]";
            event_data = event_data.replaceAll("'", '"');
            event_json = JSON.parse(event_data);

        })
        .catch(error => {
            console.error('Error:', error);
        });

}
getEvents();




//gets events from db
fetch('/api/events')
    .then(response => response.json())
    .then(data => {
        // Parses the data, making it usable
        events = "[" + String(data) + "]";
        events = events.replaceAll("'", '"');
        user_events_json = JSON.parse(events);


    })
    .catch(error => {
        console.error('Error:', error);
    });


//the global variables below keep track of important information needed in the calendar
let currentDate = new Date();
let date = new Date();
let year = date.getFullYear();
let month = date.getMonth();
let week = date.getDate() - date.getDay();

const day = document.querySelector(".calendar-dates");


const currdate = document
    .querySelector(".calendar-current-date");

const prenexIcons = document
    .querySelectorAll(".calendar-navigation span");

const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
];

const days = [
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday"
]





// Function that generates and modifies the calendar

const manipulate = () => {

    // Get the first day of the month
    let dayone = new Date(year, month, 1).getDay();

    // Get the last date of the month
    let lastdate = new Date(year, month + 1, 0).getDate();

    // Get the day of the last date of the month
    let dayend = new Date(year, month, lastdate).getDay();

    // Get the last date of the previous month
    let monthlastdate = new Date(year, month, 0).getDate();



    // Variable to store the generated calendar HTML
    let lit = "";

    if (document.getElementById("month-button").classList.contains("selected")) {

        //if statement removes the week view event scheduler when switching back to month view
        if (document.getElementById("week-background") !== null) {
            document.getElementById("week-background").remove();
        }

        // Loop to add the last dates of the previous month
        for (let i = dayone; i > 0; i--) {
            lit +=
                `<li class="inactive">${monthlastdate - i + 1}</li>`;

        }


        // Loop to add the dates of the current month
        for (let i = 1; i <= lastdate; i++) {
            //console.log(year + "-" + month + "-" + i);
            //creates a temp variable which holds the current date
            let temp = year + "-";
            if (month + 1 < 10) {
                temp += "0" + (month + 1) + "-";
            }
            else {
                temp += (month + 1) + "-";
            }

            if (i < 10) {
                temp += "0" + i;
            }
            else {
                temp += i;
            }

            // Check to see if the a day is the current date
            let isToday = i === date.getDate()
                && month === new Date().getMonth()
                && year === new Date().getFullYear()
                ? "active"
                : "";
            lit += `<li class="${temp} ${isToday}">${i}<p class="assignment-count"></p></li>`;
        }

        // Loop to add the first dates of the next month
        for (let i = dayend; i < 6; i++) {
            lit += `<li class="inactive">${i - dayend + 1}</li>`
        }

        // Update the text of the current date element 
        // with the formatted current month and year
        currdate.innerText = `${months[month]} ${year}`;

        // update the HTML of the dates element 
        // with the generated calendar
        day.innerHTML = lit;


        //else statement below handles the week view
    } else {
        //line below clears any old dates to make space for ones we are trying to view
        document.querySelector(".calendar-dates").innerHTML = "";
        let plan_id = [];
        //if statement below removes the scheduler if it is currently generated
        if (document.getElementById("week-background") !== null) {

            document.getElementById("week-background").remove();


        }

        const week_display = document.createElement("div");
        week_display.id = "week-background";



        week_display.innerHTML = `
    
                <div id="sunday" class="flex-day"></div>
                <div id="monday" class="flex-day"></div>
                <div id="tuesday" class="flex-day"></div>
                <div id="wednesday" class="flex-day"></div>
                <div id="thursday" class="flex-day"></div>
                <div id="friday" class="flex-day"></div>
                <div id="saturday" class="flex-day"></div>
    
            `;

        //appends the week display to the calendar
        document.querySelector(".calendar-dates").after(week_display);




        //for loop below removes any old events that may remain from previous weeks
        let previous_events = document.getElementsByClassName("flex-event");
        const event_count = previous_events.length;
        for (let i = 0; i < event_count; i++) {
            previous_events[0].remove();
        }


        let newdays = 0;

        let flex_days = document.getElementsByClassName("flex-day");
        let day_count = 0;

        //add the days of the current week from a previous month
        if (week < 1) {
            let i = monthlastdate + week;
            for (i; i <= monthlastdate; i++) {
                newdays += 1;
                // Check if the current date is today
                let isToday = i === currentDate.getDate()
                    && (month) === new Date().getMonth()
                    && year === new Date().getFullYear()
                    ? "active"
                    : "";

                //creates a temp variable which holds the current date
                let temp = year + "-"// + (month) + "" + i;

                if (month < 9) {
                    temp = temp + "0" + month + "-";
                }
                else {
                    temp = temp + month + "-";
                }

                if (i < 10) {
                    temp = temp + "0" + i;
                }
                else {
                    temp = temp + i;
                }

                console.log(temp);
                let the_date = new Date(year, month - 1, i).getDay();
                console.log(days[the_date]);
                flex_days[day_count].classList.add(temp);
                day_count = day_count + 1;
                console.log(flex_days[day_count - 1].classList);




                //this loop will generate all events that need to be displayed on the scheduler from a previous month
                for (let j = 0; j < Object.keys(event_json).length; j++) {
                    if (event_json[j]["date"] === temp) {
                        //lit += `<li class="${isToday}">${i + `<br>` + event_json[j]["event_description"]}</li>`;


                        //lines below are used to find the offset an object should have on the scheduler
                        const end_hour = parseInt(event_json[j]["end_time"].substring(0, 2));
                        const end_minutes = parseInt(event_json[j]["end_time"].substring(3, 5));

                        const start_hour = parseInt(event_json[j]["start_time"].substring(0, 2));
                        const start_minutes = parseInt(event_json[j]["start_time"].substring(3, 5));

                        const time_offset = start_hour * 60 + start_minutes;

                        const time_elapsed = (end_hour - start_hour) * 60 + end_minutes - start_minutes;

                        console.log("minutes elapsed: " + time_elapsed);

                        //gets the day of the week
                        const day_object = document.getElementById(days[the_date]);
                        //lines below makes the box an event is displayed in
                        let event_object = document.createElement("div");
                        event_object.classList.add("flex-event");
                        event_object.style.height = (time_elapsed - 5) + "px";
                        event_object.style.marginTop = time_offset + "px";
                        event_object.innerHTML = `${event_json[j]["event_title"]}  <br> <p class="time-data">${event_json[j]["start_time"]}-${event_json[j]["end_time"]}</p>`;
                        day_object.appendChild(event_object);
                        //Stores plan_ids for the case where a user deletes an event   
                        plan_id.push(event_json[j]["plan_id"])

                    }

                }


                lit += `<li class="${temp} ${isToday}">${i}<p class="assignment-count"></p></li>`;

            }
        }



        //adds the days of the current week
        for (let i = week; i < week + 7 && i <= lastdate; i++) {
            newdays += 1;
            if (i > 0) {
                // Check if the current date is today
                let isToday = i === currentDate.getDate()
                    && month === new Date().getMonth()
                    && year === new Date().getFullYear()
                    ? "active"
                    : "";

                //make a temp variable holding the current date in the same format as in the json, 
                //the 1 added to the month is due to month going from 0-11
                let temp = year + "-"// + (month) + "" + i;

                if (month < 9) {
                    temp = temp + "0" + (month + 1) + "-";
                }
                else {
                    temp = temp + (month + 1) + "-";
                }

                if (i < 10) {
                    temp = temp + "0" + i;
                }
                else {
                    temp = temp + i;
                }

                let the_date = new Date(year, month, i).getDay();
                flex_days[day_count].classList.add(temp);
                day_count = day_count + 1;
                console.log(flex_days[day_count - 1].classList);







                //this loop will generate all events that need to be displayed on the scheduler
                for (let j = 0; j < Object.keys(event_json).length; j++) {
                    if (event_json[j]["date"] === temp) {
                        //lit += `<li class="${isToday}">${i + `<br>` + event_json[j]["event_description"]}</li>`;

                        //lines below are used to find the offset an object should have on the scheduler
                        const end_hour = parseInt(event_json[j]["end_time"].substring(0, 2));
                        const end_minutes = parseInt(event_json[j]["end_time"].substring(3, 5));

                        const start_hour = parseInt(event_json[j]["start_time"].substring(0, 2));
                        const start_minutes = parseInt(event_json[j]["start_time"].substring(3, 5));

                        const time_offset = start_hour * 60 + start_minutes;

                        const time_elapsed = (end_hour - start_hour) * 60 + end_minutes - start_minutes;

                        console.log("minutes elapsed: " + time_elapsed);

                        //gets the day of the week
                        const day_object = document.getElementById(days[the_date]);
                        //lines below makes the box an event is displayed in
                        let event_object = document.createElement("div");
                        event_object.classList.add("flex-event");
                        event_object.style.height = (time_elapsed - 5) + "px";
                        event_object.style.marginTop = time_offset + "px";

                        event_object.innerHTML = `${event_json[j]["event_title"]}  <br> <p class="time-data">${event_json[j]["start_time"]}-${event_json[j]["end_time"]}</p>`;
                        day_object.appendChild(event_object);
                        //Stores plan_ids for the case where a user deletes an event                        
                        plan_id.push(event_json[j]["plan_id"])

                    }

                }


                lit += `<li class="${temp} ${isToday}">${i}<p class="assignment-count"></p></li>`;


            }

        }

        for (let i = 1; i < 8 - newdays; i++) {
            // Check if the current date is today
            //month below gets 1 added to it since this for loop only runs when going backwards into a new month,
            // which could lead to a flase positive on it being the current day 
            let isToday = i === currentDate.getDate()
                && month + 1 === new Date().getMonth()
                && year === new Date().getFullYear()
                ? "active"
                : "";

            //creates a temp variable which holds the current date
            let temp = year + "-"// + (month) + "" + i;

            if (month < 9) {
                temp = temp + "0" + (month + 2) + "-";
            }
            else {
                temp = temp + (month + 2) + "-";
            }

            if (i < 10) {
                temp = temp + "0" + i;
            }
            else {
                temp = temp + i;
            }
            console.log(temp);
            let the_date = new Date(year, month + 1, i).getDay();
            flex_days[day_count].classList.add(temp);
            day_count = day_count + 1;
            console.log(flex_days[day_count - 1].classList);






            //this loop will generate all events that need to be displayed on the scheduler from the next month
            for (let j = 0; j < Object.keys(event_json).length; j++) {
                if (event_json[j]["date"] === temp) {
                    //lit += `<li class="${isToday}">${i + `<br>` + event_json[j]["event_description"]}</li>`

                    //lines below are used to find the offset an object should have on the scheduler
                    const end_hour = parseInt(event_json[j]["end_time"].substring(0, 2));
                    const end_minutes = parseInt(event_json[j]["end_time"].substring(3, 5));

                    const start_hour = parseInt(event_json[j]["start_time"].substring(0, 2));
                    const start_minutes = parseInt(event_json[j]["start_time"].substring(3, 5));

                    //this offset is how many minutes into the day an event starts, and this offsets events on the scheduler by that amount
                    const time_offset = start_hour * 60 + start_minutes;

                    //This variable calculates how long an event goes on, and increases the size of an event by one pixel for every minute
                    const time_elapsed = (end_hour - start_hour) * 60 + end_minutes - start_minutes;

                    //gets the day of the week
                    const day_object = document.getElementById(days[the_date]);
                    //lines below makes the box an event is displayed in
                    let event_object = document.createElement("div");
                    event_object.classList.add("flex-event");
                    event_object.style.height = (time_elapsed - 5) + "px";
                    event_object.style.marginTop = time_offset + "px";

                    event_object.innerHTML = `${event_json[j]["event_title"]}  <br> <p class="time-data">${event_json[j]["start_time"]}-${event_json[j]["end_time"]}</p>`;
                    day_object.appendChild(event_object);

                    //Stores plan_ids for the case where a user deletes an event
                    plan_id.push(event_json[j]["plan_id"])
                }

            }


            lit += `<li class="${temp} ${isToday}">${i}<p class="assignment-count"></p></li>`;




        }

        day.innerHTML = lit;

        //retrieves all events
        const event_objects = document.querySelectorAll(".flex-event");

        
        //Loop below allows events to be modified
        for (let i = 0; i < event_objects.length; i++) {


            let event_object = document.querySelectorAll(".flex-event")[i];

            //event_object.addEventListener("click", check_events);
            event_object.addEventListener("click", async () => {

                var modal = document.getElementById("event-modify-popup");
                modal.style.display = "block";

                //let current_event = event.currentTarget;
                //console.log(document.querySelectorAll(".flex-event")[0]);

                event_info = modal.querySelector("p");
                event_info.innerHTML = event_object.innerHTML;







                var close = document.querySelector(".close");
                close.addEventListener("click", close_event);

                var delete_info = document.getElementById("plan_id");
                delete_info.value = plan_id[i];

                var modify_info = document.getElementById("plan-id");
                modify_info.value = plan_id[i];


                const form = document.getElementById("delete-form");
                //form.submit();
                //event listener below listens for and intercepts the submission of deletion of an event
                form.addEventListener("submit", async function (event) {
                    event.preventDefault();

                    const form_info = new FormData(form);

                    const response = await fetch('/study_planner', {
                        method: 'POST',
                        body: form_info,

                    })
                        .then(response => response)
                        .then(data => console.log(data))
                        .catch(error => console.log(error));

                    const func = async () => {
                        await getEvents();
                        close_event();
                        manipulate();
                    }
                    ////////////////////////
                    await func();
                })


                const modify_form = document.getElementById("modify-form");
                //form.submit();
                //event listener below listens for and intercepts the submission of modifications to an event
                modify_form.addEventListener("submit", async function (event) {
                    event.preventDefault();

                    const form_info = new FormData(modify_form);

                    const response = await fetch('/study_planner/modify', {
                        method: 'POST',
                        body: form_info,

                    })
                        .then(response => response)
                        .then(data => console.log(data))
                        .catch(error => console.log(error));

                    const func = async () => {
                        await getEvents();
                        close_event();
                        manipulate();
                    }

                    await func();
                })


            })

        }

        const day_blocks = document.querySelectorAll(".flex-day");

        console.log(day_blocks.length);

        //for loop below checks all 7 days of a week on the scheduler and checks if a user has double clicked on a day, meaning they want to make an event
        for (let i = 0; i < day_blocks.length; i++) {

            day_blocks[i].addEventListener("dblclick", event_creation);

            function event_creation() {


                //the 3 lines below allow the day of the week to be shown on the event creation modal
                var modal = document.getElementById("modal-event-add");
                modal.querySelector("h2").innerHTML = days[i];
                modal.style.display = "block";

                //retrieces day of the week and assigns it to the date field
                let temp_date = day_blocks[i].classList[1];
                console.log(temp_date);
                date_field = document.getElementById("event-date");
                date_field.value = temp_date;
                console.log(date_field);


                start_time_field = document.getElementById("event-start-time");
                end_time_field = document.getElementById("event-end-time");
                end_time_field.addEventListener("blur", time_validity_check);
                start_time_field.addEventListener("blur", time_validity_check);

                //function checks the validity of a users selected times to create an event, making sure that no bad inputs are permitted
                function time_validity_check(event) {
                    const end_time = end_time_field.value;
                    const start_time = start_time_field.value;
                    console.log(typeof end_time);
                    console.log(start_time);

                    if (start_time > end_time) {
                        end_time_field.value = '';
                    }
                    const other_events_today = day_blocks[i].querySelectorAll(".flex-event");
                    for (let j = 0; j < other_events_today.length; j++) {
                        console.log(other_events_today[j].querySelector(".time-data"));
                        let event_date_data = other_events_today[j].querySelector(".time-data").innerHTML;
                        const event_date_array = event_date_data.split("-");
                        event_date_array[0] = event_date_array[0].substring(0, 5);
                        event_date_array[1] = event_date_array[1].substring(0, 5);

                        const event_date_start = event_date_array[0].split(":");
                        const event_date_end = event_date_array[1].split(":");

                        console.log(event_date_start[1] - 1);


                        console.log(event_date_array[1]);
                        if (event_date_array[0] <= start_time && event_date_array[1] >= start_time) {
                            let start_time_revised;
                            if (event_date_end[1] != "59") {
                                start_time_revised = event_date_end[0] + ":" + String(parseInt(event_date_end[1]) + 1);
                            } else {
                                start_time_revised = (event_date_end[0] + 1) + ":00";
                            }
                            //console.log(start_time_revised);
                            start_time_field.value = start_time_revised;

                        }


                        if (event_date_array[0] > start_time && event_date_array[1] < end_time || event_date_array[0] <= end_time && event_date_array[1] >= end_time) {
                            let end_time_revised;
                            if (event_date_start[1] != "00") {
                                end_time_revised = event_date_start[0] + ":" + (event_date_start[1] - 1);
                            } else {
                                end_time_revised = (event_date_start[0] - 1) + ":59";
                            }

                            end_time_field.value = end_time_revised;

                        }

                    }

                    console.log(day_blocks[i]);


                }



                //by default the event creation type is zero, which means u can use existing events in making a planned event
                var event_type = document.getElementById("event_creation_type");
                event_type.value = 0;

                var new_event_btn = document.getElementById("new-event-btn");
                new_event_btn.addEventListener("click", new_event_displayer);

                //when activated, will allow a user to make a planned_event with a new event
                function new_event_displayer() {

                    document.getElementById("new-event-info").style.display = "block";
                    document.getElementById("old-events").style.display = "none";
                    document.getElementById("new-event-activate").style.display = "none";
                    document.getElementById("new-event-deactivate").style.display = "block";
                    document.getElementById("existing-events").style.display = "none";
                    event_type.value = 1;



                }

                var old_event_btn = document.getElementById("old-event-btn");
                old_event_btn.addEventListener("click", old_event_displayer);

                //when triggered, will allow user to make a planned_event with existing events
                function old_event_displayer() {

                    document.getElementById("new-event-info").style.display = "none";
                    document.getElementById("old-events").style.display = "block";
                    document.getElementById("new-event-deactivate").style.display = "none";
                    document.getElementById("new-event-activate").style.display = "block";
                    document.getElementById("existing-events").style.display = "block";
                    event_type.value = 0;




                }




                const add_form = document.getElementById("add-form");
                //form.submit();
                add_form.addEventListener("submit", add_event);

                //function below stops the submission of a new event, and parses the forms data
                async function add_event(event) {
                    event.preventDefault();

                    const form_info = new FormData(add_form);
                    //console.log(form_info.Date);

                    let day_date = document.querySelectorAll("li");

                    //line below updates the database with the new event
                    const response = await fetch('/study_planner/add', {
                        method: 'POST',
                        body: form_info,

                    })
                        .then(response => response)
                        .then(data => console.log(data))
                        .catch(error => console.log(error));

                    //function below resets the calendarto show new events, and deals with any rogue event listeners
                    const func = async () => {
                        await getEvents();
                        close_modals();
                        manipulate();
                        for (let i = 0; i < day_blocks.length; i++) {
                            day_blocks[i].removeEventListener("dblclick", event_creation);
                        }
                        add_form.removeEventListener("submit", add_event);
                        old_event_btn.removeEventListener("click", old_event_displayer);
                        new_event_btn.removeEventListener("click", new_event_displayer);

                    }

                    await func();

                }




                //closes modals
                var close = modal.querySelector(".close");
                close.addEventListener("click", close_modals);


                function close_modals(event) {
                    var modal = document.querySelectorAll(".modal");
                    modal[0].style.display = "none";
                    modal[1].style.display = "none";
                    modal[2].style.display = "none";

                    add_form.removeEventListener("submit", add_event);
                    old_event_btn.removeEventListener("click", old_event_displayer);
                    new_event_btn.removeEventListener("click", new_event_displayer);
                    //this_block.removeEventListener("dblclick", event_creation);

                }



                //day_blocks[i].removeEventListener("dblclick", event_creation);

            }
        }
    }

    //checks if a day on the calendar has been clicked, and pops up a modal with assignment information if applicable
    all_days = document.querySelectorAll("li");
    for (let i = 0; i < all_days.length; i++) {

        let day_id = parseInt(all_days[i].classList[0]);


        if (all_days[i].classList[0] !== "inactive" && day_id) {

            all_days[i].addEventListener("click", () => {
                day_view(all_days, i);
            });
        }

    }

    //loop below allows the number of events on a given day to be tracked and displayed on the calendar
    for (let i = 0; i < Object.keys(assignment_json).length; i++) {
        let temp_date = assignment_json[i]["due_at"].substring(0, 10);
        
        if (document.getElementsByClassName(temp_date).length !== 0) {
            let day_item = document.getElementsByClassName(temp_date)[0];
            let assignment_count = day_item.querySelector(".assignment-count").innerHTML;
            if (assignment_count.length != 0) {
                assignment_count = parseInt(assignment_count);
            } else {
                assignment_count = 0;
            }
            assignment_count += 1;
            day_item.querySelector(".assignment-count").innerHTML = String(assignment_count);
        }

    }

}



// Attach a click event listener to each icon
prenexIcons.forEach(icon => {

    // When an icon is clicked
    icon.addEventListener("click", () => {

        if (document.getElementById("month-button").classList.contains("selected")) {


            // Check if the icon is "calendar-prev"
            // or "calendar-next"
            month = icon.id === "calendar-prev" ? month - 1 : month + 1;

            // Check if the month is out of range
            if (month < 0 || month > 11) {

                // Set the date to the first day of the 
                // month with the new year
                date = new Date(year, month, new Date().getDate());

                // Set the year to the new year
                year = date.getFullYear();

                // Set the month to the new month
                month = date.getMonth();

                week = - new Date(year, month, 1).getDay() + 1;



            }

            else {

                // Set the date to the current date
                date = new Date();
                week = - new Date(year, month, 1).getDay() + 1;
                console.log(week);
            }
        }

        else {
            // Check if the icon is "calendar-prev"
            // or "calendar-next"
            week = icon.id === "calendar-prev" ? week - 7 : week + 7;

            let events = document.getElementsByClassName("flex-event");

            //This loop removes events of the last viewed week
            for (let i = events.length - 1; i >= 0; i--) {
                events[i].remove();

            }

            // Check if the icon is "calendar-prev"
            // or "calendar-next"

            // Get the last date of the month
            let lastdate = new Date(year, month + 1, 0).getDate();
            let dayend = new Date(year, month, lastdate).getDay();

            // Get the last date of the previous month
            let monthlastdate = new Date(year, month, 0).getDate();

            // Get the day of the last date of the month


            // Check if the month is out of range
            if (week < 0 || week + 7 > lastdate) {
                // week - lastdate
                week = icon.id === "calendar-prev" ? monthlastdate + week : week - lastdate;
                //change month to reflect the new month
                month = icon.id === "calendar-prev" ? month - 1 : month + 1;
                lastdate = new Date(year, month + 1, 0).getDate();
                dayend = new Date(year, month, lastdate).getDay();


                if (month < 0 || month > 11) {

                    date = new Date(year, month, new Date().getDate());

                    // Set the year to the new year
                    year = date.getFullYear();

                    // Set the month to the new month
                    month = date.getMonth();
                    currdate.innerText = `${months[month]} ${year}`;
                }
                else {
                    currdate.innerText = `${months[month]} ${year}`;
                }




                // Set the date to the first day of the 
                // month with the new year
                date = new Date(year, month, lastdate);
                console.log(date);

                // Set the year to the new year
                year = date.getFullYear();

                // Set the month to the new month
                month = date.getMonth();
            }
            else {

                // Set the date to the current date
                date = new Date();
            }





        }
        // Call the manipulate function to 
        // update the calendar display
        manipulate();
    });
});


const button = document.querySelector(".not-selected");
button.addEventListener("click", modeChange);


//This function is called to switch between the month view and week view
function modeChange(event) {

    if (event.currentTarget.classList.contains("not-selected")) {

        const otherButton = document.querySelector(".selected")
        otherButton.classList.remove("selected");
        otherButton.classList.add("not-selected");

        const modeButton = event.currentTarget
        modeButton.classList.remove("not-selected");
        modeButton.classList.add("selected");

        manipulate();
        otherButton.addEventListener("click", modeChange);
    }


}





//This function is simply called to close modals
function close_event(event) {
    var modal = document.querySelectorAll(".modal");
    modal[0].style.display = "none";
    modal[1].style.display = "none";
    modal[2].style.display = "none";
}








function formReader(event) {
    event.preventDefault();


}

//formats the day view modal
function day_view(all_days, i) {


    //let day = event.currentTarget;
    var modal = document.getElementById("modal-day-view");
    var modal_content = modal.querySelector(".modal-content-flex");
    var yesterday_btn = document.getElementById("day-prev");
    var tomorrow_btn = document.getElementById("day-next");



    while (modal_content.querySelector(".flex-assignment")) {
        modal_content.querySelector(".flex-assignment").remove();
    }


    let day_date = all_days[i].classList[0];
    for (let j = 0; j < Object.keys(assignment_json).length; j++) {

        let temp_date = assignment_json[j]["due_at"].substring(0, 10);
        if (temp_date === day_date) {
            
            let assignment_object = document.createElement("div");
            assignment_object.classList.add("flex-assignment");
            assignment_object.innerHTML = `${assignment_json[j]["name"]}-${assignment_json[j]["course_name"]}  <br> ${assignment_json[j]["due_at"]}`;
            modal_content.appendChild(assignment_object);

        }

    }

    modal.querySelector("h2").innerHTML = all_days[i].classList;
    modal.style.display = "block";

    if (all_days[i - 1].classList[0] && all_days[i - 1].classList[0] !== "inactive") {
        yesterday_btn.addEventListener("click", yesterday_click);

        function yesterday_click(event) {
            day_view(all_days, i - 1);
            yesterday_btn.removeEventListener("click", yesterday_click);
            tomorrow_btn.removeEventListener("click", tomorrow_click);
        }
    }

    if (all_days[i + 1] && all_days[i + 1].classList[0] !== "inactive") {
        tomorrow_btn.addEventListener("click", tomorrow_click);

        function tomorrow_click(event) {
            day_view(all_days, i + 1);
            tomorrow_btn.removeEventListener("click", tomorrow_click);
            yesterday_btn.removeEventListener("click", yesterday_click);
        }
    }







    var close = modal.querySelector(".close");
    close.addEventListener("click", close_day);

    function close_day() {
        var modal = document.querySelectorAll(".modal");
        modal[2].style.display = "none";
        tomorrow_btn.removeEventListener("click", tomorrow_click);
        yesterday_btn.removeEventListener("click", yesterday_click);


    }



}

