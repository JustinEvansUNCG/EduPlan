//geeks for geeks js code template was used here, though much has been added to it since then
//https://www.geeksforgeeks.org/how-to-design-a-simple-calendar-using-javascript/

let event_data;
let event_json;

let events;
let user_events_json;

//the fetch below gets the data from study_event and study_time and puts it into json format

async function getEvents() {
    console.log("test");
    await fetch('/api/event_times')
        .then(response => response.json())
        .then(data => {
            // Use the data in your JavaScript code
            event_data = "[" + String(data) + "]";
            event_data = event_data.replaceAll("'", '"');
            event_json = JSON.parse(event_data);

            console.log(event_data);


        })
        .catch(error => {
            console.error('Error:', error);
        });

}
getEvents();





fetch('/api/events')
    .then(response => response.json())
    .then(data => {
        // Use the data in your JavaScript code
        events = "[" + String(data) + "]";
        events = events.replaceAll("'", '"');
        user_events_json = JSON.parse(events);

        console.log(events);

    })
    .catch(error => {
        console.error('Error:', error);
    });



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

// Array of month names
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





// Function to generate the calendar

const manipulate = () => {

    //await getEvents();

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

            // Check if the current date is today
            let isToday = i === date.getDate()
                && month === new Date().getMonth()
                && year === new Date().getFullYear()
                ? "active"
                : "";
            lit += `<li class="${isToday}">${i}</li>`;
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
    } else {
        document.querySelector(".calendar-dates").innerHTML = "";
        let plan_id = [];

        if (document.getElementById("week-background") === null) {
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


            document.querySelector(".calendar-dates").after(week_display);

        }
        let previous_events = document.getElementsByClassName("flex-event");
        const event_count = previous_events.length;
        for (let i = 0; i < event_count; i++) {
            console.log("hello its me");

            previous_events[0].remove();
        }



        //console.log(currentD);
        //console.log(currentD.getDay());




        console.log(week);


        let newdays = 0;

        //add the days of the current week from a previous month
        if (week < 1) {
            let i = monthlastdate + week;
            for (i; i <= monthlastdate; i++) {
                newdays += 1;
                // Check if the current date is today
                //FIX BUG WITH CURRENT DAY HERE
                let isToday = i === currentDate.getDate()
                    && (month) === new Date().getMonth()
                    && year === new Date().getFullYear()
                    ? "active"
                    : "";

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



                //this needs to be implemented in the other 2 loops
                for (let j = 0; j < Object.keys(event_json).length; j++) {
                    if (event_json[j]["date"] === temp) {
                        //lit += `<li class="${isToday}">${i + `<br>` + event_json[j]["event_description"]}</li>`;
                        const day_object = document.getElementById(days[the_date]);
                        let event_object = document.createElement("div");
                        event_object.classList.add("flex-event");
                        event_object.innerHTML = `${event_json[j]["event_title"]}  <br> ${event_json[j]["start_time"]}-${event_json[j]["end_time"]}`;
                        day_object.appendChild(event_object);
                        plan_id.push(event_json[j]["plan_id"])

                    }

                }


                lit += `<li class="${isToday}">${i}</li>`;




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
                console.log(temp);
                let the_date = new Date(year, month, i).getDay();
                console.log(days[the_date]);






                //this needs to be implemented in the other 2 loops
                for (let j = 0; j < Object.keys(event_json).length; j++) {
                    if (event_json[j]["date"] === temp) {
                        //lit += `<li class="${isToday}">${i + `<br>` + event_json[j]["event_description"]}</li>`;

                        const end_hour = parseInt(event_json[j]["end_time"].substring(0, 2));
                        const end_minutes = parseInt(event_json[j]["end_time"].substring(3, 5));

                        const start_hour = parseInt(event_json[j]["start_time"].substring(0, 2));
                        const start_minutes = parseInt(event_json[j]["start_time"].substring(3, 5));

                        const time_offset = start_hour * 60 + start_minutes;

                        const time_elapsed = (end_hour - start_hour) * 60 + end_minutes - start_minutes;

                        console.log("minutes elapsed: " + time_elapsed);

                        const day_object = document.getElementById(days[the_date]);
                        let event_object = document.createElement("div");
                        event_object.classList.add("flex-event");
                        event_object.style.height = (time_elapsed - 5) + "px";
                        event_object.style.marginTop = time_offset + "px";

                        event_object.innerHTML = `${event_json[j]["event_title"]}  <br> ${event_json[j]["start_time"]}-${event_json[j]["end_time"]}`;
                        day_object.appendChild(event_object);
                        plan_id.push(event_json[j]["plan_id"])

                    }

                }


                lit += `<li class="${isToday}">${i}</li>`;


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
            console.log(days[the_date]);





            //this needs to be implemented in the other 2 loops
            for (let j = 0; j < Object.keys(event_json).length; j++) {
                if (event_json[j]["date"] === temp) {
                    //lit += `<li class="${isToday}">${i + `<br>` + event_json[j]["event_description"]}</li>`;
                    const time_elapsed = event_json[j]["end_time"].substring(0, 2);
                    console.log(time_elapsed);


                    const day_object = document.getElementById(days[the_date]);
                    let event_object = document.createElement("div");
                    event_object.classList.add("flex-event");
                    event_object.innerHTML = `${event_json[j]["event_title"]}  <br> ${event_json[j]["start_time"]}-${event_json[j]["end_time"]}`;
                    day_object.appendChild(event_object);
                    plan_id.push(event_json[j]["plan_id"])
                }

            }


            lit += `<li class="${isToday}">${i}</li>`;




        }

        day.innerHTML = lit;

        const event_objects = document.querySelectorAll(".flex-event");
        console.log(event_objects.length);
        let testnum = 0;
        for (let i = 0; i < event_objects.length; i++) {

            console.log(event_objects[i]);
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

                    await func();
                })


                const modify_form = document.getElementById("modify-form");
                //form.submit();
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

        for (let i = 0; i < day_blocks.length; i++) {

            day_blocks[i].addEventListener("dblclick", () => {


                var modal = document.getElementById("modal-event-add");
                modal.querySelector("h2").innerHTML = days[i];
                modal.style.display = "block";


                var event_type = document.getElementById("event_creation_type");
                event_type.value = 0;

                var new_event_btn = document.getElementById("new-event-btn");
                new_event_btn.addEventListener("click", () => {

                    document.getElementById("new-event-info").style.display = "block";
                    document.getElementById("old-events").style.display = "none";
                    event_type.value = 1;



                })


                const add_form = document.getElementById("add-form");
                //form.submit();
                add_form.addEventListener("submit", async function (event) {
                    event.preventDefault();

                    const form_info = new FormData(add_form);

                    const response = await fetch('/study_planner/add', {
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





                var close = modal.querySelector(".close");
                close.addEventListener("click", close_event);


            })


        }

        //event_objects.forEach(check_events);
        //event_objects.forEach(addEventListener("click", check_events));



    }
}

manipulate();

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
            console.log("hii", lastdate);

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






function close_event(event) {
    var modal = document.querySelectorAll(".modal");
    modal[0].style.display = "none";
    modal[1].style.display = "none";
}








function formReader(event) {
    event.preventDefault();


}




