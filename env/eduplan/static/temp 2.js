//geeks for geeks js code
//https://www.geeksforgeeks.org/how-to-design-a-simple-calendar-using-javascript/

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

// Function to generate the calendar

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
        console.log("testing");

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
                let isToday = i === currentDate.getDate()
                    && month === new Date().getMonth()
                    && year === new Date().getFullYear()
                    ? "active"
                    : "";
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
            lit += `<li class="${isToday}">${i}</li>`;

        }

        day.innerHTML = lit;

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
            }

            else {

                // Set the date to the current date
                date = new Date();
            }
        }

        else {
            // Check if the icon is "calendar-prev"
            // or "calendar-next"
            week = icon.id === "calendar-prev" ? week - 7 : week + 7;

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

    const otherButton = document.querySelector(".selected")
    otherButton.classList.remove("selected");
    otherButton.classList.add("not-selected");

    const modeButton = event.currentTarget
    modeButton.classList.remove("not-selected");
    modeButton.classList.add("selected");

    manipulate();
    otherButton.addEventListener("click", modeChange);
}