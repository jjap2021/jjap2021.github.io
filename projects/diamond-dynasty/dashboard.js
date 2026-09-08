const DATA_PATH =
    "../../assets/data/dynasty/";


let standings = [];
let records = {};
let streaks = [];
let rivalries = [];


let standingsSort = {
    column: "rank",
    direction: "asc"
};



/* =========================================
   LOAD DASHBOARD DATA
========================================= */

async function loadDashboard() {

    try {

        const [
            standingsResponse,
            recordsResponse,
            streaksResponse,
            rivalriesResponse
        ] = await Promise.all([

            fetch(
                DATA_PATH +
                "standings.json"
            ),

            fetch(
                DATA_PATH +
                "records.json"
            ),

            fetch(
                DATA_PATH +
                "streaks.json"
            ),

            fetch(
                DATA_PATH +
                "rivalries.json"
            )

        ]);


        if (
            !standingsResponse.ok ||
            !recordsResponse.ok ||
            !streaksResponse.ok ||
            !rivalriesResponse.ok
        ) {

            throw new Error(
                "One or more dashboard files could not be loaded."
            );
        }


        standings =
            await standingsResponse.json();

        records =
            await recordsResponse.json();

        streaks =
            await streaksResponse.json();

        rivalries =
            await rivalriesResponse.json();


        /*
         * Save the original all-time rank.
         *
         * This means clicking "#" later
         * returns the table to the original
         * standings order.
         */

        standings =
            standings.map(
                (team, index) => ({
                    ...team,
                    rank: index + 1
                })
            );


        renderGameCount();

        renderRecords();

        renderStandings();

        setupStandingsSorting();

        renderStreaks();

        setupRivalryExplorer();

    }

    catch (error) {

        console.error(
            "Dashboard failed to load:",
            error
        );


        document.body.insertAdjacentHTML(
            "afterbegin",

            `
            <div
                style="
                    background:#7f1d1d;
                    color:white;
                    padding:12px;
                    text-align:center;
                    font-family:system-ui,sans-serif;
                "
            >
                Dashboard data could not be loaded.
                Check the browser console for details.
            </div>
            `
        );
    }
}



/* =========================================
   HELPERS
========================================= */

function number(
    value,
    decimals = 2
) {

    return Number(value)
        .toFixed(decimals);
}



function pct(value) {

    return (
        Number(value) * 100
    ).toFixed(1) + "%";
}



function createCard(
    label,
    value,
    detail = ""
) {

    return `
        <div class="stat-card">

            <div class="label">
                ${label}
            </div>

            <div class="value">
                ${value}
            </div>

            <div class="detail">
                ${detail}
            </div>

        </div>
    `;
}



function gameLabel(record) {

    if (
        record.phase ===
        "Postseason"
    ) {

        return (
            `${record.season} · ` +
            `Postseason Week ${record.week}`
        );
    }


    return (
        `${record.season} · ` +
        `Week ${record.week}`
    );
}



/* =========================================
   GAME COUNT
========================================= */

function renderGameCount() {

    /*
     * Each rivalry contains every game
     * played between that pair.
     *
     * Since each game belongs to exactly
     * one unique rivalry, adding the
     * rivalry game totals gives us the
     * league-wide number of completed games.
     */

    const games =
        rivalries.reduce(
            (
                total,
                rivalry
            ) => {

                return (
                    total +
                    Number(
                        rivalry.games
                    )
                );
            },
            0
        );


    document.getElementById(
        "game-count"
    ).textContent =
        `${games} Games`;
}



/* =========================================
   RECORD BOOK
========================================= */

function renderRecords() {

    const container =
        document.getElementById(
            "record-cards"
        );


    const cards = [];


    /* BIGGEST BLOWOUT */

    if (
        records.biggest_blowout
    ) {

        const r =
            records.biggest_blowout;


        cards.push(

            createCard(

                "Biggest Blowout",

                `${number(
                    r.margin
                )} pts`,

                `${r.winner} over ` +
                `${r.loser} · ` +
                `${gameLabel(r)}`

            )

        );
    }



    /* CLOSEST GAME */

    if (
        records.closest_game
    ) {

        const r =
            records.closest_game;


        cards.push(

            createCard(

                "Closest Game",

                `${number(
                    r.margin
                )} pts`,

                `${r.winner} over ` +
                `${r.loser} · ` +
                `${gameLabel(r)}`

            )

        );
    }



    /* HIGHEST TEAM SCORE */

    if (
        records.highest_team_score
    ) {

        const r =
            records.highest_team_score;


        cards.push(

            createCard(

                "Highest Team Score",

                number(
                    r.score
                ),

                `${r.manager} · ` +
                `${gameLabel(r)}`

            )

        );
    }



    /* MOST POINTS IN A SEASON */

    if (
        records.most_points_in_season
    ) {

        const r =
            records.most_points_in_season;


        cards.push(

            createCard(

                "Most Points — Season",

                number(
                    r.points_for
                ),

                `${r.manager} · ` +
                `${r.season}`

            )

        );
    }



    /* FALLBACK */

    if (
        cards.length === 0
    ) {

        container.innerHTML =
            "<p>No record data available.</p>";

        return;
    }


    container.innerHTML =
        cards.join("");
}



/* =========================================
   ALL-TIME STANDINGS
========================================= */

function renderStandings() {

    const tbody =
        document.getElementById(
            "standings-body"
        );


    tbody.innerHTML = "";


    const sortedStandings =
        [...standings].sort(
            (a, b) => {

                const column =
                    standingsSort.column;


                const aValue =
                    a[column];

                const bValue =
                    b[column];


                /*
                 * Alphabetical sorting
                 */

                if (
                    typeof aValue ===
                    "string"
                ) {

                    if (
                        standingsSort.direction ===
                        "asc"
                    ) {

                        return (
                            aValue.localeCompare(
                                bValue
                            )
                        );
                    }


                    return (
                        bValue.localeCompare(
                            aValue
                        )
                    );
                }


                /*
                 * Numeric sorting
                 */

                if (
                    standingsSort.direction ===
                    "asc"
                ) {

                    return (
                        Number(aValue) -
                        Number(bValue)
                    );
                }


                return (
                    Number(bValue) -
                    Number(aValue)
                );
            }
        );



    sortedStandings.forEach(
        team => {

            const row =
                document.createElement(
                    "tr"
                );


            const differential =
                Number(
                    team.point_diff
                );


            row.innerHTML = `

                <td>
                    ${team.rank}
                </td>


                <td>
                    <strong>
                        ${team.manager}
                    </strong>
                </td>


                <td>
                    ${team.wins}-${team.losses}
                </td>


                <td>
                    ${pct(
                        team.win_pct
                    )}
                </td>


                <td>
                    ${number(
                        team.points_for
                    )}
                </td>


                <td>
                    ${number(
                        team.points_against
                    )}
                </td>


                <td
                    class="${
                        differential > 0
                            ? "positive"
                            : differential < 0
                                ? "negative"
                                : ""
                    }"
                >

                    ${
                        differential > 0
                            ? "+"
                            : ""
                    }

                    ${number(
                        differential
                    )}

                </td>
            `;


            tbody.appendChild(
                row
            );
        }
    );


    updateSortIndicators();
}



/* =========================================
   STANDINGS SORTING
========================================= */

function setupStandingsSorting() {

    const headers =
        document.querySelectorAll(
            "#standings th[data-sort]"
        );


    headers.forEach(
        header => {

            header.addEventListener(
                "click",
                () => {

                    const column =
                        header.dataset.sort;


                    /*
                     * Clicking the same
                     * column reverses it.
                     */

                    if (
                        standingsSort.column ===
                        column
                    ) {

                        standingsSort.direction =
                            standingsSort.direction ===
                            "asc"
                                ? "desc"
                                : "asc";
                    }


                    /*
                     * Clicking a new column
                     * selects a sensible
                     * default direction.
                     */

                    else {

                        standingsSort.column =
                            column;


                        if (
                            column === "manager" ||
                            column === "rank"
                        ) {

                            standingsSort.direction =
                                "asc";
                        }

                        else {

                            standingsSort.direction =
                                "desc";
                        }
                    }


                    renderStandings();
                }
            );
        }
    );
}



function updateSortIndicators() {

    const headers =
        document.querySelectorAll(
            "#standings th[data-sort]"
        );


    headers.forEach(
        header => {

            const icon =
                header.querySelector(
                    ".sort-icon"
                );


            header.classList.remove(
                "active-sort"
            );


            if (
                header.dataset.sort ===
                standingsSort.column
            ) {

                header.classList.add(
                    "active-sort"
                );


                icon.textContent =
                    standingsSort.direction ===
                    "asc"
                        ? "▲"
                        : "▼";
            }


            else {

                icon.textContent = "";
            }
        }
    );
}



/* =========================================
   STREAKS
========================================= */

function renderStreaks() {

    const container =
        document.getElementById(
            "streak-cards"
        );


    if (
        streaks.length === 0
    ) {

        container.innerHTML =
            "<p>No streak data available.</p>";

        return;
    }



    const longestWin =
        [...streaks].sort(
            (a, b) =>

                Number(
                    b.longest_win_streak
                ) -

                Number(
                    a.longest_win_streak
                )
        )[0];



    const longestLoss =
        [...streaks].sort(
            (a, b) =>

                Number(
                    b.longest_loss_streak
                ) -

                Number(
                    a.longest_loss_streak
                )
        )[0];



    const activeWin =
        [...streaks]

            .filter(
                team =>
                    team.current_streak_type ===
                    "W"
            )

            .sort(
                (a, b) =>

                    Number(
                        b.current_streak
                    ) -

                    Number(
                        a.current_streak
                    )
            )[0];



    const cards = [];


    if (longestWin) {

        cards.push(

            createCard(

                "Longest Win Streak",

                `${longestWin.longest_win_streak} games`,

                longestWin.manager

            )

        );
    }



    if (longestLoss) {

        cards.push(

            createCard(

                "Longest Losing Streak",

                `${longestLoss.longest_loss_streak} games`,

                longestLoss.manager

            )

        );
    }



    if (activeWin) {

        cards.push(

            createCard(

                "Longest Active Win Streak",

                `${activeWin.current_streak} games`,

                activeWin.manager

            )

        );
    }


    container.innerHTML =
        cards.join("");
}



/* =========================================
   RIVALRY EXPLORER SETUP
========================================= */

function setupRivalryExplorer() {

    const managerOne =
        document.getElementById(
            "manager-one"
        );


    const managerTwo =
        document.getElementById(
            "manager-two"
        );


    const managers =
        standings

            .map(
                team =>
                    team.manager
            )

            .sort(
                (a, b) =>
                    a.localeCompare(b)
            );



    managers.forEach(
        manager => {

            managerOne.add(
                new Option(
                    manager,
                    manager
                )
            );


            managerTwo.add(
                new Option(
                    manager,
                    manager
                )
            );
        }
    );



    managerOne.addEventListener(
        "change",
        renderSelectedRivalry
    );


    managerTwo.addEventListener(
        "change",
        renderSelectedRivalry
    );
}



/* =========================================
   FIND SELECTED RIVALRY
========================================= */

function renderSelectedRivalry() {

    const first =
        document.getElementById(
            "manager-one"
        ).value;


    const second =
        document.getElementById(
            "manager-two"
        ).value;


    const container =
        document.getElementById(
            "rivalry-result"
        );


    if (
        !first ||
        !second
    ) {

        container.innerHTML =
            "<p>Select two franchises above.</p>";

        return;
    }


    if (
        first === second
    ) {

        container.innerHTML =
            "<p>Select two different franchises.</p>";

        return;
    }



    const rivalry =
        rivalries.find(
            r => {

                const direct =
                    r.manager_1 === first &&
                    r.manager_2 === second;


                const reverse =
                    r.manager_1 === second &&
                    r.manager_2 === first;


                return (
                    direct ||
                    reverse
                );
            }
        );


    if (
        !rivalry
    ) {

        container.innerHTML =
            "<p>No rivalry data found.</p>";

        return;
    }


    renderRivalry(
        rivalry,
        first,
        second
    );
}



/* =========================================
   RENDER RIVALRY
========================================= */

function renderRivalry(
    rivalry,
    first,
    second
) {

    const firstIsManagerOne =
        rivalry.manager_1 ===
        first;



    const firstWins =
        firstIsManagerOne

            ? rivalry.manager_1_wins

            : rivalry.manager_2_wins;



    const secondWins =
        firstIsManagerOne

            ? rivalry.manager_2_wins

            : rivalry.manager_1_wins;



    const firstPoints =
        firstIsManagerOne

            ? rivalry.manager_1_points

            : rivalry.manager_2_points;



    const secondPoints =
        firstIsManagerOne

            ? rivalry.manager_2_points

            : rivalry.manager_1_points;



    const firstAvg =
        firstIsManagerOne

            ? rivalry.avg_manager_1_score

            : rivalry.avg_manager_2_score;



    const secondAvg =
        firstIsManagerOne

            ? rivalry.avg_manager_2_score

            : rivalry.avg_manager_1_score;



    const firstPostseasonWins =
        firstIsManagerOne

            ? rivalry.manager_1_postseason_wins

            : rivalry.manager_2_postseason_wins;



    const secondPostseasonWins =
        firstIsManagerOne

            ? rivalry.manager_2_postseason_wins

            : rivalry.manager_1_postseason_wins;



    const container =
        document.getElementById(
            "rivalry-result"
        );



    container.innerHTML = `

        <div class="rivalry-header">

            <div>

                <div class="eyebrow">
                    ${rivalry.games}
                    Meetings
                </div>

                <h3>
                    ${first}
                    vs
                    ${second}
                </h3>

            </div>


            <div class="rivalry-record">
                ${firstWins} – ${secondWins}
            </div>

        </div>



        <div class="rivalry-stats">


            <div class="rivalry-stat">

                <strong>
                    ${number(firstAvg)}
                    –
                    ${number(secondAvg)}
                </strong>

                <span>
                    Average Score
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${number(firstPoints)}
                    –
                    ${number(secondPoints)}
                </strong>

                <span>
                    All-Time Points
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${rivalry.postseason_meetings}
                </strong>

                <span>
                    Postseason Meetings
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${firstPostseasonWins}
                    –
                    ${secondPostseasonWins}
                </strong>

                <span>
                    Postseason-Week Record
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${rivalry.current_streak_manager}
                    W${rivalry.current_streak}
                </strong>

                <span>
                    Current Rivalry Streak
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${rivalry.longest_streak_manager}
                    W${rivalry.longest_streak}
                </strong>

                <span>
                    Longest Rivalry Streak
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${number(
                        rivalry.closest_game.margin
                    )}
                    pts
                </strong>

                <span>
                    Closest Game ·
                    ${gameLabel(
                        rivalry.closest_game
                    )}
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${number(
                        rivalry.biggest_blowout.margin
                    )}
                    pts
                </strong>

                <span>
                    Biggest Blowout ·
                    ${gameLabel(
                        rivalry.biggest_blowout
                    )}
                </span>

            </div>



            <div class="rivalry-stat">

                <strong>
                    ${number(
                        rivalry.highest_scoring_game.total_points
                    )}
                    pts
                </strong>

                <span>
                    Highest-Scoring Meeting ·
                    ${gameLabel(
                        rivalry.highest_scoring_game
                    )}
                </span>

            </div>


        </div>
    `;
}



/* =========================================
   START DASHBOARD
========================================= */

loadDashboard();