const DATA_PATH =
    "../../assets/data/dynasty/";


const DATA_FILES = {

    standings:
        "standings.json",

    records:
        "records.json",

    streaks:
        "streaks.json",

    rivalries:
        "rivalries.json",

    summary:
        "summary.json",

    tradeStats:
        "trade_stats.json",

    tradeHistory:
        "trade_history.json",

    pickButterfly:
        "pick_butterfly.json",

    playerHistory:
        "player_history.json",

        playerHistoryIndex:
        "player_history_index.json",

    scoringEras:
        "scoring_eras.json",
};


let standingsData = [];
let rivalryData = [];
let tradeHistoryData = [];
let pickButterflyData = [];

let playerHistoryData = [];
let playerHistoryIndexData = [];
let selectedPlayerId = null;


let scoringErasData = {
    methodology: {},
    league_eras: [],
    franchise_seasons: [],
};


let scoringSort = {
    key: "score_index",
    direction: "desc",
};


let filteredPickData = [];


let standingsSort = {

    key:
        "rank",

    direction:
        "asc",
};


/* ==========================================================
   GENERIC HELPERS
========================================================== */

async function loadJSON(file) {

    const response =
        await fetch(
            DATA_PATH + file
        );


    if (!response.ok) {

        throw new Error(
            `Could not load ${file}`
        );
    }


    return response.json();
}


function safeArray(value) {

    return Array.isArray(value)
        ? value
        : [];
}


function firstDefined(
    ...values
) {

    return values.find(
        value =>
            value !== undefined
            &&
            value !== null
            &&
            value !== ""
    );
}


function formatNumber(
    value,
    decimals = 2
) {

    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {
        return "—";
    }


    return number.toLocaleString(
        undefined,
        {
            minimumFractionDigits:
                decimals,

            maximumFractionDigits:
                decimals,
        }
    );
}


function formatInteger(value) {

    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {
        return "—";
    }


    return number.toLocaleString();
}


function formatPct(value) {

    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {
        return "—";
    }


    return number.toFixed(3);
}


function formatSigned(value) {

    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {
        return "—";
    }


    const sign =
        number > 0
            ? "+"
            : "";


    return (
        sign
        + number.toFixed(2)
    );
}


function valueClass(value) {

    const number =
        Number(value);


    if (
        number > 0
    ) {
        return "positive";
    }


    if (
        number < 0
    ) {
        return "negative";
    }


    return "";
}


function formatDate(
    isoDate
) {

    if (!isoDate) {

        return "Unknown date";
    }


    const date =
        new Date(isoDate);


    return date.toLocaleDateString(
        undefined,
        {
            year:
                "numeric",

            month:
                "short",

            day:
                "numeric",
        }
    );
}


function getManager(row) {

    return firstDefined(

        row.manager,

        row.franchise,

        row.name,

        row.team,

        "Unknown"
    );
}


/* ==========================================================
   TABS
========================================================== */

function activateTab(
    targetTab
) {

    const buttons =
        document.querySelectorAll(
            ".dashboard-nav .tab-button"
        );


    const panels =
        document.querySelectorAll(
            ".tab-panel"
        );


    buttons.forEach(
        button => {

            const isActive =
                button.dataset.tab
                === targetTab;


            button.classList.toggle(
                "active",
                isActive
            );


            button.setAttribute(
                "aria-selected",
                isActive
                    ? "true"
                    : "false"
            );
        }
    );


    panels.forEach(
        panel => {

            panel.classList.toggle(
                "active",
                panel.id === targetTab
            );
        }
    );
}


function setupTabs() {

    const buttons =
        document.querySelectorAll(
            ".dashboard-nav .tab-button"
        );


    if (
        !buttons.length
    ) {

        console.warn(
            "No dashboard tab buttons found."
        );

        return;
    }


    buttons.forEach(
        button => {

            button.setAttribute(
                "type",
                "button"
            );


            button.setAttribute(
                "role",
                "tab"
            );


            button.addEventListener(
                "click",
                event => {

                    event.preventDefault();


                    const target =
                        button.dataset.tab;


                    if (!target) {
                        return;
                    }


                    activateTab(
                        target
                    );
                }
            );
        }
    );


    const activeButton =
        document.querySelector(
            ".dashboard-nav .tab-button.active"
        );


    const initialTab =
        activeButton?.dataset.tab
        ?? buttons[0].dataset.tab;


    activateTab(
        initialTab
    );
}


/* ==========================================================
   HERO
========================================================== */

function renderHero(
    summary,
    tradeStats
) {

    const gameCount =
        firstDefined(

            summary.completed_games,

            summary.games,

            summary.total_games,

            324
        );


    document
        .getElementById(
            "heroGameCount"
        )
        .textContent =
        formatInteger(
            gameCount
        );


    const totalTrades =
        firstDefined(

            tradeStats?.summary
                ?.total_trades,

            tradeHistoryData.length,

            0
        );


    document
        .getElementById(
            "heroTradeCount"
        )
        .textContent =
        formatInteger(
            totalTrades
        );
}


/* ==========================================================
   STANDINGS
========================================================== */

function renderStandings() {

    const body =
        document.getElementById(
            "standingsBody"
        );


    body.innerHTML =
        "";


    const sorted = [
        ...standingsData
    ];


    sorted.sort(
        (a, b) => {

            const key =
                standingsSort.key;


            let aValue =
                key === "rank"
                    ? a.originalRank
                    : (
                        key === "manager"
                            ? getManager(a)
                            : a[key]
                    );


            let bValue =
                key === "rank"
                    ? b.originalRank
                    : (
                        key === "manager"
                            ? getManager(b)
                            : b[key]
                    );


            if (
                typeof aValue
                === "string"
            ) {

                const result =
                    aValue.localeCompare(
                        bValue
                    );


                return (
                    standingsSort.direction
                    === "asc"
                        ? result
                        : -result
                );
            }


            aValue =
                Number(
                    aValue ?? 0
                );


            bValue =
                Number(
                    bValue ?? 0
                );


            return (
                standingsSort.direction
                === "asc"
                    ? aValue - bValue
                    : bValue - aValue
            );
        }
    );


    sorted.forEach(
        row => {

            const pointDiff =
                firstDefined(

                    row.point_diff,

                    row.point_differential,

                    0
                );


            const tr =
                document.createElement(
                    "tr"
                );


            tr.innerHTML = `

                <td>
                    ${row.originalRank}
                </td>

                <td class="franchise-cell">
                    ${getManager(row)}
                </td>

                <td>
                    ${row.wins}
                </td>

                <td>
                    ${row.losses}
                </td>

                <td>
                    ${formatPct(
                        row.win_pct
                    )}
                </td>

                <td>
                    ${formatNumber(
                        row.points_for
                    )}
                </td>

                <td>
                    ${formatNumber(
                        row.points_against
                    )}
                </td>

                <td class="${valueClass(
                    pointDiff
                )}">
                    ${formatSigned(
                        pointDiff
                    )}
                </td>
            `;


            body.appendChild(
                tr
            );
        }
    );
}


function setupStandingsSorting() {

    document
        .querySelectorAll(
            "#standingsTable th[data-sort]"
        )
        .forEach(
            header => {

                header.addEventListener(
                    "click",
                    () => {

                        const key =
                            header.dataset.sort;


                        if (
                            standingsSort.key
                            === key
                        ) {

                            standingsSort.direction =
                                standingsSort.direction
                                === "asc"
                                    ? "desc"
                                    : "asc";

                        } else {

                            standingsSort.key =
                                key;


                            standingsSort.direction =
                                (
                                    key === "manager"
                                    ||
                                    key === "rank"
                                )
                                    ? "asc"
                                    : "desc";
                        }


                        renderStandings();
                    }
                );
            }
        );
}


/* ==========================================================
   RECORD BOOK HELPERS
========================================================== */

function recordTeamOne(
    record
) {

    return firstDefined(

        record.winner,

        record.team,

        record.manager,

        record.franchise,

        record.team_1,

        record.team1,

        record.manager_1,

        record.manager1,

        record.franchise_1,

        record.franchise1,

        record.high_team,

        record.highest_team
    );
}


function recordTeamTwo(
    record
) {

    return firstDefined(

        record.loser,

        record.opponent,

        record.team_2,

        record.team2,

        record.manager_2,

        record.manager2,

        record.franchise_2,

        record.franchise2,

        record.low_team
    );
}


function recordScoreOne(
    record
) {

    return firstDefined(

        record.winner_score,

        record.score,

        record.team_score,

        record.points,

        record.points_for,

        record.team_1_score,

        record.team1_score,

        record.manager_1_score,

        record.score_1,

        record.score1,

        record.high_score
    );
}


function recordScoreTwo(
    record
) {

    return firstDefined(

        record.loser_score,

        record.opponent_score,

        record.team_2_score,

        record.team2_score,

        record.manager_2_score,

        record.score_2,

        record.score2,

        record.low_score
    );
}


function recordTotal(
    record,
    score1,
    score2
) {

    const stored =
        firstDefined(

            record.total_score,

            record.total_points,

            record.combined_score,

            record.combined_points,

            record.game_total
        );


    if (
        stored !== undefined
    ) {
        return stored;
    }


    if (
        score1 !== undefined
        &&
        score2 !== undefined
    ) {

        return (
            Number(score1)
            +
            Number(score2)
        );
    }


    return undefined;
}


function recordMeta(record) {

    const parts =
        [];


    if (
        record.season !== undefined
    ) {

        parts.push(
            record.season
        );
    }


    if (
        record.week !== undefined
    ) {

        parts.push(
            `Week ${record.week}`
        );
    }


    const phase =
        firstDefined(

            record.phase,

            record.game_type,

            record.scope
        );


    if (phase) {

        parts.push(
            phase
        );
    }


    return parts.join(
        " · "
    );
}


/* ==========================================================
   RECORD BOOK
========================================================== */

function gameRecordCard(
    label,
    record,
    mode
) {

    if (!record) {
        return "";
    }


    const team1 =
        recordTeamOne(
            record
        );


    const team2 =
        recordTeamTwo(
            record
        );


    const score1 =
        recordScoreOne(
            record
        );


    const score2 =
        recordScoreTwo(
            record
        );


    let main =
        "";


    let value =
        "";


    if (
        mode === "score"
    ) {

        main = `

            ${team1 ?? "Unknown"}

            ${
                score1 !== undefined
                    ? formatNumber(
                        score1
                    )
                    : ""
            }

            –

            ${
                score2 !== undefined
                    ? formatNumber(
                        score2
                    )
                    : ""
            }

            ${team2 ?? "Unknown"}
        `;


        const margin =
            firstDefined(

                record.margin,

                (
                    score1 !== undefined
                    &&
                    score2 !== undefined
                        ? Math.abs(
                            Number(score1)
                            -
                            Number(score2)
                        )
                        : undefined
                )
            );


        if (
            margin !== undefined
        ) {

            value =
                `Margin ${formatNumber(
                    margin
                )}`;
        }

    } else if (
        mode === "total"
    ) {

        main = `

            ${team1 ?? "Unknown"}

            ${
                score1 !== undefined
                    ? formatNumber(
                        score1
                    )
                    : ""
            }

            –

            ${
                score2 !== undefined
                    ? formatNumber(
                        score2
                    )
                    : ""
            }

            ${team2 ?? "Unknown"}
        `;


        const total =
            recordTotal(
                record,
                score1,
                score2
            );


        if (
            total !== undefined
        ) {

            value =
                `Total ${formatNumber(
                    total
                )}`;
        }

    } else if (
        mode === "team"
    ) {

        main = `

            ${team1 ?? "Unknown"}

            ${
                score1 !== undefined
                    ? formatNumber(
                        score1
                    )
                    : ""
            }
        `;


        if (team2) {

            value =
                `vs ${team2}`;
        }
    }


    return `

        <article class="record-card">

            <p class="record-label">
                ${label}
            </p>

            <div class="record-main">
                ${main}
            </div>

            <div class="record-value">
                ${value}
            </div>

            <p class="record-detail">
                ${recordMeta(record)}
            </p>

        </article>
    `;
}


function seasonRecordCard(
    label,
    record,
    valueKeys,
    formatter
) {

    if (!record) {
        return "";
    }


    const manager =
        getManager(
            record
        );


    const value =
        firstDefined(
            ...valueKeys.map(
                key =>
                    record[key]
            )
        );


    const recordText =
        (
            record.wins !== undefined
            &&
            record.losses !== undefined
        )
            ? (
                ` · ${record.wins}-${record.losses}`
            )
            : "";


    return `

        <article class="record-card">

            <p class="record-label">
                ${label}
            </p>

            <div class="record-main">
                ${manager}
            </div>

            <div class="record-value">
                ${
                    value !== undefined
                        ? formatter(
                            value
                        )
                        : "—"
                }
            </div>

            <p class="record-detail">

                ${record.season ?? ""}

                ${recordText}

            </p>

        </article>
    `;
}


function renderRecords(records) {

    const grid =
        document.getElementById(
            "recordGrid"
        );


    grid.innerHTML = [

        gameRecordCard(

            "Biggest Blowout",

            records.biggest_blowout,

            "score"
        ),


        gameRecordCard(

            "Closest Game",

            records.closest_game,

            "score"
        ),


        gameRecordCard(

            "Highest Scoring Game",

            records.highest_scoring_game,

            "total"
        ),


        gameRecordCard(

            "Lowest Scoring Game",

            records.lowest_scoring_game,

            "total"
        ),


        gameRecordCard(

            "Highest Team Score",

            records.highest_team_score,

            "team"
        ),


        gameRecordCard(

            "Lowest Team Score",

            records.lowest_team_score,

            "team"
        ),


        seasonRecordCard(

            "Most Points in a Season",

            records.most_points_in_season,

            [
                "points_for",
                "points",
                "score"
            ],

            value =>
                formatNumber(
                    value
                )
        ),


        seasonRecordCard(

            "Best Season Win %",

            records.best_win_pct_season,

            [
                "win_pct",
                "winning_percentage"
            ],

            value =>
                formatPct(
                    value
                )
        ),


        seasonRecordCard(

            "Best Season Point Diff",

            records.best_point_diff_season,

            [
                "point_diff",
                "point_differential"
            ],

            value =>
                formatSigned(
                    value
                )
        ),


        seasonRecordCard(

            "Worst Season Point Diff",

            records.worst_point_diff_season,

            [
                "point_diff",
                "point_differential"
            ],

            value =>
                formatSigned(
                    value
                )
        ),

    ].join("");
}


/* ==========================================================
   STREAKS
========================================================== */

function renderStreaks(
    streaks
) {

    const body =
        document.getElementById(
            "streaksBody"
        );


    const rows =
        Array.isArray(streaks)

            ? streaks

            : Object.entries(
                streaks
            ).map(

                (
                    [
                        manager,
                        values
                    ]
                ) => ({

                    manager,

                    ...values,
                })
            );


    body.innerHTML =
        "";


    rows
        .sort(
            (a, b) =>

                getManager(a)
                    .localeCompare(
                        getManager(b)
                    )
        )
        .forEach(
            row => {

                const longestWin =
                    firstDefined(

                        row.longest_win_streak,

                        row.longest_winning_streak,

                        row.longest_win,

                        0
                    );


                const longestLoss =
                    firstDefined(

                        row.longest_loss_streak,

                        row.longest_losing_streak,

                        row.longest_loss,

                        0
                    );


                const current =
                    firstDefined(

                        row.current_streak,

                        "—"
                    );


                const tr =
                    document.createElement(
                        "tr"
                    );


                tr.innerHTML = `

                    <td class="franchise-cell">

                        ${getManager(row)}

                    </td>


                    <td>

                        W${longestWin}

                    </td>


                    <td>

                        L${longestLoss}

                    </td>


                    <td>

                        ${current}

                    </td>
                `;


                body.appendChild(
                    tr
                );
            }
        );
}


/* ==========================================================
   RIVALRIES
========================================================== */

function getRivalryTeams() {

    const teams =
        new Set();


    rivalryData.forEach(
        rivalry => {

            const team1 =
                firstDefined(

                    rivalry.manager_1,

                    rivalry.franchise_1,

                    rivalry.team_1
                );


            const team2 =
                firstDefined(

                    rivalry.manager_2,

                    rivalry.franchise_2,

                    rivalry.team_2
                );


            if (team1) {
                teams.add(team1);
            }


            if (team2) {
                teams.add(team2);
            }
        }
    );


    return [
        ...teams
    ].sort();
}


function setupRivalrySelectors() {

    const team1 =
        document.getElementById(
            "rivalryTeam1"
        );


    const team2 =
        document.getElementById(
            "rivalryTeam2"
        );


    const teams =
        getRivalryTeams();


    const options =
        teams
            .map(
                team => `

                    <option value="${team}">
                        ${team}
                    </option>
                `
            )
            .join("");


    team1.innerHTML =
        options;


    team2.innerHTML =
        options;


    if (
        teams.length > 1
    ) {

        team2.selectedIndex =
            1;
    }


    team1.addEventListener(
        "change",
        renderSelectedRivalry
    );


    team2.addEventListener(
        "change",
        renderSelectedRivalry
    );


    renderSelectedRivalry();
}


function findRivalry(
    team1,
    team2
) {

    return rivalryData.find(
        rivalry => {

            const a =
                firstDefined(

                    rivalry.manager_1,

                    rivalry.franchise_1,

                    rivalry.team_1
                );


            const b =
                firstDefined(

                    rivalry.manager_2,

                    rivalry.franchise_2,

                    rivalry.team_2
                );


            return (

                (
                    a === team1
                    &&
                    b === team2
                )

                ||

                (
                    a === team2
                    &&
                    b === team1
                )
            );
        }
    );
}


function renderSelectedRivalry() {

    const team1 =
        document.getElementById(
            "rivalryTeam1"
        ).value;


    const team2 =
        document.getElementById(
            "rivalryTeam2"
        ).value;


    const container =
        document.getElementById(
            "rivalryResults"
        );


    if (
        team1 === team2
    ) {

        container.innerHTML = `

            <div class="card empty-state">

                Select two different franchises.

            </div>
        `;

        return;
    }


    const rivalry =
        findRivalry(
            team1,
            team2
        );


    if (!rivalry) {

        container.innerHTML = `

            <div class="card empty-state">

                No rivalry data found.

            </div>
        `;

        return;
    }


    const storedTeam1 =
        firstDefined(

            rivalry.manager_1,

            rivalry.franchise_1,

            rivalry.team_1
        );


    let wins1 =
        firstDefined(

            rivalry.team_1_wins,

            rivalry.manager_1_wins,

            rivalry.wins_1,

            0
        );


    let wins2 =
        firstDefined(

            rivalry.team_2_wins,

            rivalry.manager_2_wins,

            rivalry.wins_2,

            0
        );


    if (
        storedTeam1 !== team1
    ) {

        [
            wins1,
            wins2
        ] = [
            wins2,
            wins1
        ];
    }


    const games =
        firstDefined(

            rivalry.games,

            rivalry.total_games,

            (
                Number(wins1)
                +
                Number(wins2)
            )
        );


    const postseason =
        firstDefined(

            rivalry.postseason_meetings,

            rivalry.postseason_games,

            0
        );


    const pointDiff =
        firstDefined(

            rivalry.point_differential,

            rivalry.point_diff,

            0
        );


    const currentStreak =
        firstDefined(

            rivalry.current_streak,

            "—"
        );


    container.innerHTML = `

        <div class="card rivalry-header-card">

            <h3 class="rivalry-title">

                ${team1}

                <span>
                    vs
                </span>

                ${team2}

            </h3>


            <p class="rivalry-record">

                ${wins1}-${wins2}

            </p>

        </div>


        <div class="metric-grid">


            <div class="metric-card">

                <span class="metric-value">
                    ${games}
                </span>

                <span class="metric-label">
                    Meetings
                </span>

            </div>


            <div class="metric-card">

                <span class="metric-value">
                    ${postseason}
                </span>

                <span class="metric-label">
                    Postseason-Week Meetings
                </span>

            </div>


            <div class="metric-card">

                <span
                    class="
                        metric-value
                        ${valueClass(
                            pointDiff
                        )}
                    "
                >

                    ${formatSigned(
                        pointDiff
                    )}

                </span>

                <span class="metric-label">
                    Point Differential
                </span>

            </div>


            <div class="metric-card">

                <span class="metric-value">
                    ${currentStreak}
                </span>

                <span class="metric-label">
                    Current Streak
                </span>

            </div>

        </div>
    `;
}


/* ==========================================================
   TRADE SUMMARY
========================================================== */

function renderTradeSummary(
    tradeStats
) {

    const summary =
        tradeStats.summary
        ?? {};


    const franchiseStats =
        safeArray(
            tradeStats.by_franchise
        );


    const totalTrades =
        firstDefined(

            summary.total_trades,

            tradeHistoryData.length,

            0
        );


    const totalPlayerMoves =
        franchiseStats.reduce(

            (
                sum,
                row
            ) =>

                sum
                +
                Number(
                    row.players_acquired
                    ?? 0
                ),

            0
        );


    const totalPickMoves =
        franchiseStats.reduce(

            (
                sum,
                row
            ) =>

                sum
                +
                Number(
                    row.picks_acquired
                    ?? 0
                ),

            0
        );


    const mostActive =
        franchiseStats[0]
            ?.franchise
        ?? "—";


    document
        .getElementById(
            "tradeSummaryGrid"
        )
        .innerHTML = `


            <div class="trade-summary-card">

                <span class="trade-summary-value">
                    ${totalTrades}
                </span>

                <span class="trade-summary-label">
                    Completed Trades
                </span>

            </div>


            <div class="trade-summary-card">

                <span class="trade-summary-value">
                    ${totalPlayerMoves}
                </span>

                <span class="trade-summary-label">
                    Player Movements
                </span>

            </div>


            <div class="trade-summary-card">

                <span class="trade-summary-value">
                    ${totalPickMoves}
                </span>

                <span class="trade-summary-label">
                    Draft Pick Movements
                </span>

            </div>


            <div class="trade-summary-card">

                <span class="trade-summary-value">
                    ${mostActive}
                </span>

                <span class="trade-summary-label">
                    Most Active Trader
                </span>

            </div>
        `;
}


/* ==========================================================
   TRADE RANKINGS
========================================================== */

function rankingHTML(
    rows,
    nameFunction,
    valueFunction,
    detailFunction
) {

    return rows
        .map(
            (
                row,
                index
            ) => `

                <div class="ranking-row">

                    <span class="rank-number">
                        ${index + 1}
                    </span>


                    <div>

                        <div class="ranking-name">

                            ${nameFunction(
                                row
                            )}

                        </div>


                        <div class="ranking-detail">

                            ${detailFunction(
                                row
                            )}

                        </div>

                    </div>


                    <div class="ranking-value">

                        ${valueFunction(
                            row
                        )}

                    </div>

                </div>
            `
        )
        .join("");
}


function renderTradeRankings(
    tradeStats
) {

    const franchises =
        safeArray(
            tradeStats.by_franchise
        )
            .slice(
                0,
                10
            );


    document
        .getElementById(
            "tradeFranchiseList"
        )
        .innerHTML =
        rankingHTML(

            franchises,

            row =>
                row.franchise,

            row =>
                row.trades,

            row =>
                `${row.players_acquired} players acquired · ${row.picks_acquired} picks acquired`
        );


    const partners =
        safeArray(
            tradeStats.trade_partners
        )
            .slice(
                0,
                10
            );


    document
        .getElementById(
            "tradePartnerList"
        )
        .innerHTML =
        rankingHTML(

            partners,

            row =>
                `${row.franchise_1} ↔ ${row.franchise_2}`,

            row =>
                row.trades,

            () =>
                "completed trades"
        );


    const players =
        safeArray(
            tradeStats.player_trade_counts
        )
            .slice(
                0,
                10
            );


    document
        .getElementById(
            "tradedPlayerList"
        )
        .innerHTML =
        rankingHTML(

            players,

            row =>
                row.name,

            row =>
                row.trade_movements,

            row =>
                `${row.position ?? "—"} · ${row.times_acquired} acquisitions`
        );
}


/* ==========================================================
   PICK BUTTERFLY FILTERS
========================================================== */

function pickHumanName(
    pick
) {

    return (
        `${pick.original_franchise} `
        +
        `${pick.pick_season} `
        +
        `Round ${pick.round}`
    );
}


function pickOptionLabel(
    pick
) {

    const result =
        pick.draft_resolved

            ? (
                `${pick.draft.player_name} `
                +
                `(${pick.draft.display_pick})`
            )

            : "Future Pick";


    return (
        `${pickHumanName(pick)}`
        +
        ` — ${pick.times_traded} trade`
        +
        (
            pick.times_traded === 1
                ? ""
                : "s"
        )
        +
        ` — ${result}`
    );
}


function populatePickFilters() {

    const seasonSelect =
        document.getElementById(
            "pickSeasonFilter"
        );


    const roundSelect =
        document.getElementById(
            "pickRoundFilter"
        );


    const franchiseSelect =
        document.getElementById(
            "pickFranchiseFilter"
        );


    const seasons = [
        ...new Set(
            pickButterflyData.map(
                pick =>
                    pick.pick_season
            )
        )
    ]
        .sort(
            (a, b) =>
                b - a
        );


    seasons.forEach(
        season => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                season;


            option.textContent =
                season;


            seasonSelect.appendChild(
                option
            );
        }
    );


    const rounds = [
        ...new Set(
            pickButterflyData.map(
                pick =>
                    pick.round
            )
        )
    ]
        .sort(
            (a, b) =>
                a - b
        );


    rounds.forEach(
        round => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                round;


            option.textContent =
                `Round ${round}`;


            roundSelect.appendChild(
                option
            );
        }
    );


    const franchises = [
        ...new Set(
            pickButterflyData.map(
                pick =>
                    pick.original_franchise
            )
        )
    ]
        .sort();


    franchises.forEach(
        franchise => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                franchise;


            option.textContent =
                franchise;


            franchiseSelect.appendChild(
                option
            );
        }
    );
}


function getFilteredPicks() {

    const search =
        document
            .getElementById(
                "pickSearch"
            )
            .value
            .trim()
            .toLowerCase();


    const season =
        document
            .getElementById(
                "pickSeasonFilter"
            )
            .value;


    const round =
        document
            .getElementById(
                "pickRoundFilter"
            )
            .value;


    const franchise =
        document
            .getElementById(
                "pickFranchiseFilter"
            )
            .value;


    return pickButterflyData.filter(
        pick => {

            const seasonMatch =
                (
                    season === "all"
                    ||
                    String(
                        pick.pick_season
                    ) === season
                );


            const roundMatch =
                (
                    round === "all"
                    ||
                    String(
                        pick.round
                    ) === round
                );


            const franchiseMatch =
                (
                    franchise === "all"
                    ||
                    pick.original_franchise
                    === franchise
                );


            const searchable =
                [

                    pick.pick_id,

                    pick.original_franchise,

                    pick.current_franchise,

                    pick.pick_season,

                    pick.round,

                    pick.draft?.player_name,

                    pick.draft?.display_pick,

                    pick.draft?.drafted_by_franchise,

                ]
                    .filter(
                        value =>
                            value !== undefined
                            &&
                            value !== null
                    )
                    .join(" ")
                    .toLowerCase();


            const searchMatch =
                (
                    !search
                    ||
                    searchable.includes(
                        search
                    )
                );


            return (
                seasonMatch
                &&
                roundMatch
                &&
                franchiseMatch
                &&
                searchMatch
            );
        }
    );
}


function refreshPickSelector() {

    filteredPickData =
        getFilteredPicks();


    const select =
        document.getElementById(
            "pickButterflySelect"
        );


    const count =
        document.getElementById(
            "pickResultCount"
        );


    count.textContent =
        filteredPickData.length;


    if (
        !filteredPickData.length
    ) {

        select.innerHTML = `

            <option value="">
                No matching picks
            </option>
        `;


        document
            .getElementById(
                "pickButterflyResult"
            )
            .innerHTML = `

                <div class="empty-state">

                    No pick assets match those filters.

                </div>
            `;


        return;
    }


    select.innerHTML =
        filteredPickData
            .map(
                (
                    pick,
                    index
                ) => `

                    <option value="${index}">

                        ${pickOptionLabel(
                            pick
                        )}

                    </option>
                `
            )
            .join("");


    renderPickButterfly();
}


function setupPickButterfly() {

    populatePickFilters();


    const controls = [

        document.getElementById(
            "pickSearch"
        ),

        document.getElementById(
            "pickSeasonFilter"
        ),

        document.getElementById(
            "pickRoundFilter"
        ),

        document.getElementById(
            "pickFranchiseFilter"
        ),
    ];


    controls.forEach(
        control => {

            control.addEventListener(
                control.tagName === "INPUT"
                    ? "input"
                    : "change",

                refreshPickSelector
            );
        }
    );


    document
        .getElementById(
            "pickButterflySelect"
        )
        .addEventListener(
            "change",
            renderPickButterfly
        );


    refreshPickSelector();
}


/* ==========================================================
   ASSET LABELS
========================================================== */

function assetLabel(
    asset
) {

    if (
        asset.type === "player"
    ) {

        return asset.name;
    }


    if (
        asset.type === "pick"
    ) {

        return (
            `${asset.original_franchise} `
            +
            `${asset.season} `
            +
            `R${asset.round}`
        );
    }


    if (
        asset.type === "faab"
    ) {

        return (
            `${asset.amount} FAAB`
        );
    }


    return "Unknown asset";
}


/* ==========================================================
   BUTTERFLY TRADE DETAIL
========================================================== */

function miniTradeHTML(
    trade
) {

    if (
        !trade
        ||
        !safeArray(
            trade.teams
        ).length
    ) {

        return "";
    }


    return `

        <div class="timeline-trade-assets">

            ${
                trade.teams
                    .map(
                        team => {

                            const received =
                                safeArray(
                                    team.received
                                );


                            return `

                                <div class="trade-side-mini">

                                    <strong>

                                        ${team.franchise}
                                        received

                                    </strong>


                                    ${
                                        received.length

                                            ? received
                                                .map(
                                                    asset => `

                                                        <div class="asset-mini">

                                                            ${assetLabel(
                                                                asset
                                                            )}

                                                        </div>
                                                    `
                                                )
                                                .join("")

                                            : `

                                                <div class="asset-mini">

                                                    No listed assets

                                                </div>
                                            `
                                    }

                                </div>
                            `;
                        }
                    )
                    .join("")
            }

        </div>
    `;
}


/* ==========================================================
   BUTTERFLY RENDERING
========================================================== */

function renderPickButterfly() {

    const select =
        document.getElementById(
            "pickButterflySelect"
        );


    const index =
        Number(
            select.value
        );


    const pick =
        filteredPickData[
            index
        ];


    const container =
        document.getElementById(
            "pickButterflyResult"
        );


    if (!pick) {

        container.innerHTML = `

            <div class="empty-state">

                No pick data found.

            </div>
        `;

        return;
    }


    const draft =
        pick.draft;


    const finalValue =
        pick.draft_resolved

            ? (
                `${draft.display_pick} `
                +
                `${draft.player_name}`
            )

            : (
                `${pick.pick_season} `
                +
                `Round ${pick.round}`
            );


    const finalFranchise =
        pick.draft_resolved

            ? draft.drafted_by_franchise

            : pick.current_franchise;


    const timeline =
        safeArray(
            pick.movements
        )
            .map(
                movement => `

                    <div class="timeline-item">


                        <div class="timeline-dot"></div>


                        <div class="timeline-content">


                            <p class="timeline-transfer">

                                ${movement.from_franchise}

                                →

                                ${movement.to_franchise}

                            </p>


                            <p class="timeline-meta">

                                ${formatDate(
                                    movement.created
                                )}

                                ·

                                ${movement.league_season}
                                Season

                            </p>


                            ${miniTradeHTML(
                                movement.trade
                            )}


                        </div>

                    </div>
                `
            )
            .join("");


    let draftHTML =
        "";


    if (
        pick.draft_resolved
    ) {

        draftHTML = `

            <div class="draft-destination">


                <div class="timeline-dot"></div>


                <div class="draft-destination-content">


                    <p class="section-kicker">

                        DRAFT RESULT

                    </p>


                    <div class="draft-result-player">

                        ${draft.display_pick}

                        ·

                        ${draft.player_name}

                    </div>


                    <div class="ranking-detail">

                        Drafted by

                        ${draft.drafted_by_franchise}

                        ·

                        ${draft.position ?? "—"}

                        ${
                            draft.nfl_team

                                ? ` · ${draft.nfl_team}`

                                : ""
                        }

                    </div>


                </div>

            </div>
        `;

    } else {

        draftHTML = `

            <div class="draft-destination">


                <div class="timeline-dot"></div>


                <div class="draft-destination-content">


                    <p class="section-kicker">

                        CURRENT STATUS

                    </p>


                    <div class="draft-result-player">

                        Future

                        ${pick.pick_season}

                        Round ${pick.round}

                        Pick

                    </div>


                    <div class="ranking-detail">

                        Currently held by

                        ${pick.current_franchise}

                    </div>


                </div>

            </div>
        `;
    }


    container.innerHTML = `


        <div class="butterfly-overview">


            <div class="butterfly-stat">

                <span class="butterfly-stat-value">

                    ${pick.original_franchise}

                </span>

                <span class="butterfly-stat-label">

                    Original Franchise

                </span>

            </div>


            <div class="butterfly-stat">

                <span class="butterfly-stat-value">

                    ${pick.times_traded}

                </span>

                <span class="butterfly-stat-label">

                    Times Traded

                </span>

            </div>


            <div class="butterfly-stat">

                <span class="butterfly-stat-value">

                    ${finalFranchise}

                </span>

                <span class="butterfly-stat-label">

                    Final / Current Holder

                </span>

            </div>


            <div class="butterfly-stat">

                <span class="butterfly-stat-value">

                    ${finalValue}

                </span>

                <span class="butterfly-stat-label">

                    Draft Result

                </span>

            </div>


        </div>


        <div class="pick-timeline">

            ${timeline}

            ${draftHTML}

        </div>
    `;
}


/* ==========================================================
   TRADE HISTORY FILTERS
========================================================== */

function setupTradeHistoryFilters() {

    const seasonSelect =
        document.getElementById(
            "tradeSeasonFilter"
        );


    const franchiseSelect =
        document.getElementById(
            "tradeFranchiseFilter"
        );


    const seasons = [

        ...new Set(

            tradeHistoryData.map(
                trade =>
                    trade.season
            )
        )
    ]
        .sort(
            (a, b) =>
                b - a
        );


    seasons.forEach(
        season => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                season;


            option.textContent =
                season;


            seasonSelect.appendChild(
                option
            );
        }
    );


    const franchises = [

        ...new Set(

            tradeHistoryData.flatMap(
                trade =>

                    safeArray(
                        trade.teams
                    )
                        .map(
                            team =>
                                team.franchise
                        )
            )
        )
    ]
        .sort();


    franchises.forEach(
        franchise => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                franchise;


            option.textContent =
                franchise;


            franchiseSelect.appendChild(
                option
            );
        }
    );


    seasonSelect.addEventListener(
        "change",
        renderTradeHistory
    );


    franchiseSelect.addEventListener(
        "change",
        renderTradeHistory
    );


    renderTradeHistory();
}


/* ==========================================================
   TRADE CARD
========================================================== */

function tradeSideHTML(
    team
) {

    const received =
        safeArray(
            team.received
        );


    return `

        <div class="trade-side">


            <h4>

                ${team.franchise}

                received

            </h4>


            <div class="asset-list">

                ${
                    received.length

                        ? received
                            .map(
                                asset => `

                                    <div class="asset-item">

                                        <span class="asset-type">

                                            ${asset.type}

                                        </span>

                                        ${assetLabel(
                                            asset
                                        )}

                                    </div>
                                `
                            )
                            .join("")

                        : `

                            <div class="asset-item">

                                No listed assets

                            </div>
                        `
                }

            </div>


        </div>
    `;
}


/* ==========================================================
   TRADE HISTORY
========================================================== */

function renderTradeHistory() {

    const seasonFilter =
        document
            .getElementById(
                "tradeSeasonFilter"
            )
            .value;


    const franchiseFilter =
        document
            .getElementById(
                "tradeFranchiseFilter"
            )
            .value;


    const container =
        document.getElementById(
            "tradeHistoryList"
        );


    const filtered =
        tradeHistoryData
            .filter(
                trade => {

                    const seasonMatch =
                        (
                            seasonFilter
                            === "all"

                            ||

                            String(
                                trade.season
                            )
                            === seasonFilter
                        );


                    const franchiseMatch =
                        (
                            franchiseFilter
                            === "all"

                            ||

                            safeArray(
                                trade.teams
                            )
                                .some(
                                    team =>
                                        team.franchise
                                        === franchiseFilter
                                )
                        );


                    return (
                        seasonMatch
                        &&
                        franchiseMatch
                    );
                }
            )
            .sort(
                (a, b) =>

                    (
                        b.created_timestamp
                        ?? 0
                    )

                    -

                    (
                        a.created_timestamp
                        ?? 0
                    )
            );


    if (
        !filtered.length
    ) {

        container.innerHTML = `

            <div class="card empty-state">

                No trades match those filters.

            </div>
        `;

        return;
    }


    container.innerHTML =
        filtered
            .map(
                trade => `

                    <article class="trade-card">


                        <div class="trade-card-header">


                            <div class="trade-card-season">

                                ${trade.season}

                                Trade

                            </div>


                            <div class="trade-card-date">

                                ${formatDate(
                                    trade.created
                                )}

                            </div>


                        </div>


                        <div class="trade-sides">

                            ${
                                safeArray(
                                    trade.teams
                                )
                                    .map(
                                        tradeSideHTML
                                    )
                                    .join("")
                            }

                        </div>


                    </article>
                `
            )
            .join("");
}



/* ==========================================================
   PLAYER HISTORY
========================================================== */

function escapeHTML(value) {

    return String(
        value ?? ""
    )
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function playerEventLabel(type) {

    const labels = {

        draft:
            "Drafted",

        trade:
            "Trade",

        waiver_add:
            "Waiver Claim",

        free_agent_add:
            "Free Agent Add",

        drop:
            "Dropped",
    };


    return labels[type]
        ?? type
        ?? "Transaction";
}


function playerEventDate(event) {

    return firstDefined(

        event.timestamp,

        event.created,

        event.date,

        null
    );
}


function playerEventFranchise(event) {

    return firstDefined(

        event.franchise,

        event.drafted_by_franchise,

        event.to_franchise,

        event.from_franchise,

        "Unknown"
    );
}


function playerEventDescription(event) {

    const type =
        event.type;


    if (
        type === "draft"
    ) {

        const franchise =
            firstDefined(

                event.drafted_by_franchise,

                event.franchise,

                event.owner_after,

                "Unknown"
            );


        const pick =
            firstDefined(

                event.display_pick,

                event.pick,

                event.pick_number
            );


        return (
            `Drafted by <strong>${escapeHTML(
                franchise
            )}</strong>`
            +
            (
                pick
                    ? ` at ${escapeHTML(pick)}`
                    : ""
            )
        );
    }


    if (
        type === "trade"
    ) {

        return `

            <strong>
                ${escapeHTML(
                    event.from_franchise
                    ?? event.owner_before
                    ?? "Unknown"
                )}
            </strong>

            →

            <strong>
                ${escapeHTML(
                    event.to_franchise
                    ?? event.owner_after
                    ?? "Unknown"
                )}
            </strong>
        `;
    }


    if (
        type === "waiver_add"
    ) {

        return `

            Claimed by

            <strong>
                ${escapeHTML(
                    event.franchise
                    ?? event.owner_after
                    ?? "Unknown"
                )}
            </strong>
        `;
    }


    if (
        type === "free_agent_add"
    ) {

        return `

            Added by

            <strong>
                ${escapeHTML(
                    event.franchise
                    ?? event.owner_after
                    ?? "Unknown"
                )}
            </strong>
        `;
    }


    if (
        type === "drop"
    ) {

        return `

            Dropped by

            <strong>
                ${escapeHTML(
                    event.franchise
                    ?? event.owner_before
                    ?? "Unknown"
                )}
            </strong>
        `;
    }


    return escapeHTML(
        playerEventFranchise(
            event
        )
    );
}


function playerDraftText(player) {

    const draft =
        player.draft_origin;


    if (!draft) {

        return (
            "Not drafted in recorded league history"
        );
    }


    const parts =
        [];


    if (
        draft.season
    ) {

        parts.push(
            String(
                draft.season
            )
        );
    }


    const pick =
        firstDefined(

            draft.display_pick,

            draft.pick,

            draft.pick_number
        );


    if (pick) {

        parts.push(
            `Pick ${pick}`
        );

    } else if (
        draft.round
    ) {

        parts.push(
            `Round ${draft.round}`
        );
    }


    const draftedBy =
        firstDefined(

            draft.drafted_by_franchise,

            draft.franchise
        );


    if (draftedBy) {

        parts.push(
            `by ${draftedBy}`
        );
    }


    return parts.join(
        " · "
    );
}


function playerSearchText(player) {

    return [

        player.name,

        player.position,

        player.nfl_team,

        player.current_franchise,

        ...safeArray(
            player.franchises_owned_by
        ),

    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
}


function renderPlayerSearchResults(
    query = ""
) {

    const container =
        document.getElementById(
            "playerSearchResults"
        );


    const count =
        document.getElementById(
            "playerResultCount"
        );


    if (
        !container
        ||
        !count
    ) {

        return;
    }


    const normalized =
        query
            .trim()
            .toLowerCase();


    let matches =
        playerHistoryIndexData.filter(
            player =>

                !normalized

                ||

                playerSearchText(
                    player
                ).includes(
                    normalized
                )
        );


    matches.sort(
        (a, b) =>

            (
                a.name
                ?? ""
            )
                .localeCompare(
                    b.name
                    ?? ""
                )
    );


    count.textContent =
        normalized
            ? `${formatInteger(
                matches.length
            )} / ${formatInteger(
                playerHistoryIndexData.length
            )}`
            : formatInteger(
                playerHistoryIndexData.length
            );


    if (!normalized) {

        container.innerHTML = `

            <div class="player-search-prompt">

                Start typing to search
                ${formatInteger(
                    playerHistoryIndexData.length
                )}
                players.

            </div>
        `;

        return;
    }


    if (
        !matches.length
    ) {

        container.innerHTML = `

            <div class="player-search-prompt">

                No players matched
                “${escapeHTML(
                    query
                )}”.

            </div>
        `;

        return;
    }


    const visible =
        matches.slice(
            0,
            12
        );


    container.innerHTML =
        visible
            .map(
                player => `

                    <button
                        type="button"
                        class="
                            player-result-row
                            ${
                                String(
                                    player.player_id
                                )
                                ===
                                String(
                                    selectedPlayerId
                                )
                                    ? "active"
                                    : ""
                            }
                        "
                        data-player-id="${escapeHTML(
                            player.player_id
                        )}"
                    >

                        <span class="player-result-main">

                            <strong>
                                ${escapeHTML(
                                    player.name
                                    ?? "Unknown Player"
                                )}
                            </strong>

                            <span>

                                ${escapeHTML(
                                    player.position
                                    ?? "—"
                                )}

                                ${
                                    player.nfl_team
                                        ? ` · ${escapeHTML(
                                            player.nfl_team
                                        )}`
                                        : ""
                                }

                            </span>

                        </span>


                        <span class="player-result-owner">

                            ${
                                player.current_franchise

                                    ? `Current: ${escapeHTML(
                                        player.current_franchise
                                    )}`

                                    : "Free Agent"
                            }

                        </span>

                    </button>
                `
            )
            .join("");


    if (
        matches.length
        >
        visible.length
    ) {

        container.insertAdjacentHTML(

            "beforeend",

            `

                <div class="player-search-more">

                    ${
                        matches.length
                        -
                        visible.length
                    }
                    more matches —
                    keep typing to narrow the search.

                </div>
            `
        );
    }


    container
        .querySelectorAll(
            ".player-result-row"
        )
        .forEach(
            button => {

                button.addEventListener(

                    "click",

                    () => {

                        selectPlayer(
                            button.dataset.playerId
                        );
                    }
                );
            }
        );
}

function findTradeForPlayerEvent(
    event
) {

    if (
        event.type !== "trade"
    ) {

        return null;
    }


    const transactionId =
        firstDefined(

            event.transaction_id,

            event.transactionId,

            event.id
        );


    if (!transactionId) {

        return null;
    }


    return tradeHistoryData.find(
        trade =>

            String(
                firstDefined(

                    trade.transaction_id,

                    trade.transactionId,

                    trade.id
                )
            )

            ===

            String(
                transactionId
            )
    )
    ?? null;
}


function playerTimelineTradeHTML(
    event
) {

    const trade =
        findTradeForPlayerEvent(
            event
        );


    if (!trade) {

        return "";
    }


    const teams =
        safeArray(
            trade.teams
        );


    if (!teams.length) {

        return "";
    }


    return `

        <div class="player-timeline-trade">

            <div class="player-timeline-trade-heading">

                Full Trade

            </div>


            <div class="trade-sides">

                ${
                    teams
                        .map(
                            tradeSideHTML
                        )
                        .join("")
                }

            </div>

        </div>
    `;
}

function renderPlayerDetail(
    player
) {

    const container =
        document.getElementById(
            "playerDetail"
        );


    if (
        !container
        ||
        !player
    ) {

        return;
    }


    const currentOwner =
        player.current_franchise
        ?? "Free Agent";


    const ownership =
        safeArray(
            player.franchises_owned_by
        );


    const events =
        safeArray(
            player.events
        );


    const metrics = [

        [
            "Trades",
            player.trade_count
            ?? 0
        ],

        [
            "Waiver Adds",
            player.waiver_count
            ?? 0
        ],

        [
            "FA Adds",
            player.free_agent_count
            ?? 0
        ],

        [
            "Drops",
            player.drop_count
            ?? 0
        ],
    ];


    container.innerHTML = `

        <article class="card player-profile-card">

            <div class="player-profile-header">

                <div>

                    <p class="section-kicker">
                        PLAYER PROFILE
                    </p>

                    <h3>
                        ${escapeHTML(
                            player.name
                            ?? "Unknown Player"
                        )}
                    </h3>

                    <p class="player-position-line">

                        ${escapeHTML(
                            player.position
                            ?? "—"
                        )}

                        ${
                            player.nfl_team
                                ? ` · ${escapeHTML(
                                    player.nfl_team
                                )}`
                                : ""
                        }

                    </p>

                </div>


                <div class="player-current-owner">

                    <span>
                        Current Franchise
                    </span>

                    <strong>
                        ${escapeHTML(
                            currentOwner
                        )}
                    </strong>

                </div>

            </div>


            <div class="player-metric-grid">

                ${
                    metrics
                        .map(
                            (
                                [
                                    label,
                                    value
                                ]
                            ) => `

                                <div class="player-metric-card">

                                    <span class="player-metric-value">
                                        ${formatInteger(
                                            value
                                        )}
                                    </span>

                                    <span class="player-metric-label">
                                        ${label}
                                    </span>

                                </div>
                            `
                        )
                        .join("")
                }

            </div>


            <div class="player-profile-grid">

                <div>

                    <span class="player-info-label">
                        Draft Origin
                    </span>

                    <strong>
                        ${escapeHTML(
                            playerDraftText(
                                player
                            )
                        )}
                    </strong>

                </div>


                <div>

                    <span class="player-info-label">
                        Franchises Owned By
                    </span>

                    <strong>
                        ${formatInteger(
                            ownership.length
                        )}
                    </strong>

                </div>


                <div>

                    <span class="player-info-label">
                        Recorded Events
                    </span>

                    <strong>
                        ${formatInteger(
                            events.length
                        )}
                    </strong>

                </div>

            </div>


            <div class="ownership-path-block">

                <span class="player-info-label">
                    Ownership Path
                </span>

                <div class="ownership-path">

                    ${
                        ownership.length

                            ? ownership
                                .map(
                                    (
                                        owner,
                                        index
                                    ) => `

                                        ${
                                            index

                                                ? `
                                                    <span class="ownership-arrow">
                                                        →
                                                    </span>
                                                `

                                                : ""
                                        }

                                        <span class="ownership-chip">
                                            ${escapeHTML(
                                                owner
                                            )}
                                        </span>
                                    `
                                )
                                .join("")

                            : `

                                <span class="player-muted">
                                    No franchise ownership recorded.
                                </span>
                            `
                    }

                </div>

            </div>

        </article>


        <div class="
            subsection-heading
            player-timeline-heading
        ">

            <div>

                <p class="section-kicker">
                    CAREER LOG
                </p>

                <h3>
                    League Timeline
                </h3>

            </div>

            <p>
                ${formatInteger(
                    events.length
                )}
                recorded league events.
            </p>

        </div>


        <div class="player-timeline">

            ${
                events.length

                    ? events
                        .map(
                            event => {

                                const eventDate =
                                    playerEventDate(
                                        event
                                    );


                                return `

                                    <article
                                        class="
                                            card
                                            player-timeline-event
                                            player-event-${escapeHTML(
                                                event.type
                                                ?? "transaction"
                                            )}
                                        "
                                    >

                                        <div class="player-timeline-marker"></div>


                                        <div class="player-timeline-content">

                                            <div class="player-timeline-topline">

                                                <span class="player-event-type">

                                                    ${escapeHTML(
                                                        playerEventLabel(
                                                            event.type
                                                        )
                                                    )}

                                                </span>


                                                <span class="player-event-date">

                                                    ${
                                                        eventDate

                                                            ? formatDate(
                                                                eventDate
                                                            )

                                                            : (
                                                                event.season
                                                                ?? "Unknown date"
                                                            )
                                                    }

                                                </span>

                                            </div>


                                            <div class="player-event-description">

                                                ${playerEventDescription(
                                                    event
                                                )}

                                            </div>


                                            ${
                                                event.type === "trade"

                                                    ? playerTimelineTradeHTML(
                                                        event
                                                    )

                                                    : ""
                                            }


                                            <div class="player-event-meta">

                                                ${
                                                    event.season
                                                        ? escapeHTML(
                                                            event.season
                                                        )
                                                        : ""
                                                }

                                                ${
                                                    event.type === "draft"
                                                    &&
                                                    event.original_franchise
                                                    &&
                                                    event.original_franchise
                                                    !==
                                                    firstDefined(
                                                        event.drafted_by_franchise,
                                                        event.franchise
                                                    )

                                                        ? ` · Original pick: ${escapeHTML(
                                                            event.original_franchise
                                                        )}`

                                                        : ""
                                                }

                                            </div>

                                        </div>

                                    </article>
                                `;
                            }
                        )
                        .join("")

                    : `

                        <div class="card empty-state">
                            No player events found.
                        </div>
                    `
            }

        </div>
    `;
}


function selectPlayer(
    playerId
) {

    const player =
        playerHistoryData.find(
            item =>

                String(
                    item.player_id
                )

                ===

                String(
                    playerId
                )
        );


    if (!player) {

        return;
    }


    selectedPlayerId =
        String(
            playerId
        );


    renderPlayerDetail(
        player
    );


    const search =
        document.getElementById(
            "playerSearch"
        );


    renderPlayerSearchResults(
        search?.value
        ?? ""
    );
}


function setupPlayerSearch() {

    const input =
        document.getElementById(
            "playerSearch"
        );


    if (!input) {

        return;
    }


    renderPlayerSearchResults(
        ""
    );


    input.addEventListener(

        "input",

        () => {

            renderPlayerSearchResults(
                input.value
            );
        }
    );


    input.addEventListener(

        "keydown",

        event => {

            if (
                event.key
                !== "Enter"
            ) {

                return;
            }


            const firstResult =
                document.querySelector(
                    ".player-result-row"
                );


            if (firstResult) {

                event.preventDefault();


                selectPlayer(
                    firstResult.dataset.playerId
                );
            }
        }
    );
}


/* ==========================================================
   INITIALIZATION
========================================================== */

async function initializeDashboard() {

    try {

        const [

            standings,

            records,

            streaks,

            rivalries,

            summary,

            tradeStats,

            tradeHistory,

            pickButterfly,

            playerHistory,

            playerHistoryIndex,

            scoringEras,

        ] = await Promise.all([


            loadJSON(
                DATA_FILES.standings
            ),


            loadJSON(
                DATA_FILES.records
            ),


            loadJSON(
                DATA_FILES.streaks
            ),


            loadJSON(
                DATA_FILES.rivalries
            ),


            loadJSON(
                DATA_FILES.summary
            ),


            loadJSON(
                DATA_FILES.tradeStats
            ),


            loadJSON(
                DATA_FILES.tradeHistory
            ),


            loadJSON(
                DATA_FILES.pickButterfly
            ),


            loadJSON(
                DATA_FILES.playerHistory
            ),


            loadJSON(
                DATA_FILES.playerHistoryIndex
            ),

            loadJSON(
                DATA_FILES.scoringEras
            ),

        ]);


        standingsData =
            standings.map(
                (
                    row,
                    index
                ) => ({

                    ...row,

                    originalRank:
                        row.rank
                        ?? index + 1,
                })
            );


        rivalryData =
            rivalries;


        tradeHistoryData =
            tradeHistory;


        pickButterflyData =
            pickButterfly;


        playerHistoryData =
            safeArray(
                playerHistory
            );


        playerHistoryIndexData =
            safeArray(
                playerHistoryIndex
            );

        scoringErasData =
            scoringEras
            ??
            {
                methodology: {},
                league_eras: [],
                franchise_seasons: [],
            };


        setupTabs();


        renderHero(
            summary,
            tradeStats
        );


        renderStandings();


        setupStandingsSorting();


        renderRecords(
            records
        );


        renderStreaks(
            streaks
        );


        setupRivalrySelectors();


        renderTradeSummary(
            tradeStats
        );


        renderTradeRankings(
            tradeStats
        );


        setupPickButterfly();


        setupTradeHistoryFilters();


        setupScoringControls();


        renderScoringEras();


        setupPlayerSearch();


    } catch (error) {

        console.error(

            "Dashboard initialization failed:",

            error
        );


        document.body.insertAdjacentHTML(

            "beforeend",

            `

                <div
                    style="
                        position: fixed;
                        left: 20px;
                        right: 20px;
                        bottom: 20px;
                        padding: 16px;
                        background: #3b1117;
                        border: 1px solid #8e2f3b;
                        color: #ffdce0;
                        border-radius: 12px;
                        z-index: 9999;
                    "
                >

                    Dashboard data failed to load.
                    Check the browser console for details.

                </div>
            `
        );
    }
}

/* ==========================================================
   SCORING & ERAS
========================================================== */

function scoringValueClass(
    value,
    baseline = 0
) {

    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {
        return "";
    }


    if (
        number > baseline
    ) {
        return "positive";
    }


    if (
        number < baseline
    ) {
        return "negative";
    }


    return "";
}



function renderScoringSummary() {

    const grid =
        document.getElementById(
            "scoringSummaryGrid"
        );


    if (!grid) {
        return;
    }


    const eras =
        safeArray(
            scoringErasData.league_eras
        );


    const seasons =
        safeArray(
            scoringErasData.franchise_seasons
        );


    if (
        !eras.length
        ||
        !seasons.length
    ) {

        grid.innerHTML =
            "";

        return;
    }


    const highestEra =
        [...eras].sort(
            (a, b) =>
                Number(
                    b.league_ppg
                )
                -
                Number(
                    a.league_ppg
                )
        )[0];


    const lowestEra =
        [...eras].sort(
            (a, b) =>
                Number(
                    a.league_ppg
                )
                -
                Number(
                    b.league_ppg
                )
        )[0];


    const bestSeason =
        [...seasons].sort(
            (a, b) =>
                Number(
                    b.score_index
                )
                -
                Number(
                    a.score_index
                )
        )[0];


    const bestPpgPlus =
        [...seasons].sort(
            (a, b) =>
                Number(
                    b.ppg_plus
                )
                -
                Number(
                    a.ppg_plus
                )
        )[0];


    grid.innerHTML = `

        <article class="scoring-summary-card">

            <span class="scoring-summary-label">
                Highest-Scoring Era
            </span>

            <strong class="scoring-summary-value">
                ${highestEra.season}
            </strong>

            <span class="scoring-summary-detail">
                ${formatNumber(
                    highestEra.league_ppg,
                    2
                )} league PPG
            </span>

        </article>


        <article class="scoring-summary-card">

            <span class="scoring-summary-label">
                Lowest-Scoring Era
            </span>

            <strong class="scoring-summary-value">
                ${lowestEra.season}
            </strong>

            <span class="scoring-summary-detail">
                ${formatNumber(
                    lowestEra.league_ppg,
                    2
                )} league PPG
            </span>

        </article>


        <article class="scoring-summary-card">

            <span class="scoring-summary-label">
                Best Score Index
            </span>

            <strong class="scoring-summary-value">
                ${formatNumber(
                    bestSeason.score_index,
                    1
                )}
            </strong>

            <span class="scoring-summary-detail">
                ${bestSeason.manager}
                ·
                ${bestSeason.season}
            </span>

        </article>


        <article class="scoring-summary-card">

            <span class="scoring-summary-label">
                Best PPG+
            </span>

            <strong class="scoring-summary-value">
                ${formatNumber(
                    bestPpgPlus.ppg_plus,
                    1
                )}
            </strong>

            <span class="scoring-summary-detail">
                ${bestPpgPlus.manager}
                ·
                ${bestPpgPlus.season}
            </span>

        </article>
    `;
}



function renderLeaguePpgChart() {

    const container =
        document.getElementById(
            "leaguePpgChart"
        );


    if (!container) {
        return;
    }


    const data =
        [
            ...safeArray(
                scoringErasData.league_eras
            )
        ].sort(
            (a, b) =>
                Number(
                    a.season
                )
                -
                Number(
                    b.season
                )
        );


    if (!data.length) {

        container.innerHTML =
            "<p>No scoring era data available.</p>";

        return;
    }


    const width =
        720;

    const height =
        310;

    const padLeft =
        58;

    const padRight =
        24;

    const padTop =
        28;

    const padBottom =
        48;


    const values =
        data.map(
            row =>
                Number(
                    row.league_ppg
                )
        );


    const rawMin =
        Math.min(
            ...values
        );


    const rawMax =
        Math.max(
            ...values
        );


    const range =
        Math.max(
            rawMax - rawMin,
            1
        );


    const minY =
        Math.floor(
            rawMin
            -
            range * 0.25
        );


    const maxY =
        Math.ceil(
            rawMax
            +
            range * 0.25
        );


    const xFor =
        index =>

            data.length === 1

                ? width / 2

                : (
                    padLeft
                    +
                    index
                    *
                    (
                        (
                            width
                            -
                            padLeft
                            -
                            padRight
                        )
                        /
                        (
                            data.length
                            -
                            1
                        )
                    )
                );


    const yFor =
        value =>

            padTop
            +
            (
                (
                    maxY
                    -
                    value
                )
                /
                (
                    maxY
                    -
                    minY
                )
            )
            *
            (
                height
                -
                padTop
                -
                padBottom
            );


    const points =
        data.map(
            (
                row,
                index
            ) =>

                `${xFor(index)},${yFor(
                    Number(
                        row.league_ppg
                    )
                )}`
        ).join(
            " "
        );


    const ticks =
        4;


    const gridLines =
        Array.from(
            {
                length:
                    ticks + 1
            },

            (
                _,
                index
            ) => {

                const value =
                    minY
                    +
                    (
                        (
                            maxY
                            -
                            minY
                        )
                        *
                        index
                        /
                        ticks
                    );


                const y =
                    yFor(
                        value
                    );


                return `

                    <line
                        x1="${padLeft}"
                        y1="${y}"
                        x2="${width - padRight}"
                        y2="${y}"
                        class="scoring-chart-grid"
                    />


                    <text
                        x="${padLeft - 12}"
                        y="${y + 4}"
                        text-anchor="end"
                        class="scoring-chart-axis"
                    >
                        ${value.toFixed(0)}
                    </text>
                `;
            }
        ).join(
            ""
        );


    const pointMarkup =
        data.map(
            (
                row,
                index
            ) => {

                const x =
                    xFor(
                        index
                    );


                const y =
                    yFor(
                        Number(
                            row.league_ppg
                        )
                    );


                return `

                    <circle
                        cx="${x}"
                        cy="${y}"
                        r="5"
                        class="scoring-chart-point"
                    />


                    <text
                        x="${x}"
                        y="${y - 14}"
                        text-anchor="middle"
                        class="scoring-chart-value"
                    >
                        ${formatNumber(
                            row.league_ppg,
                            1
                        )}
                    </text>


                    <text
                        x="${x}"
                        y="${height - 18}"
                        text-anchor="middle"
                        class="
                            scoring-chart-axis
                            scoring-chart-season
                        "
                    >
                        ${row.season}
                    </text>
                `;
            }
        ).join(
            ""
        );


    container.innerHTML = `

        <svg
            viewBox="0 0 ${width} ${height}"
            role="img"
            aria-label="League points per game by season"
        >

            ${gridLines}


            <polyline
                points="${points}"
                class="scoring-chart-line"
            />


            ${pointMarkup}

        </svg>
    `;
}



function renderScoringLeaderboard() {

    const container =
        document.getElementById(
            "scoringLeaderboard"
        );


    if (!container) {
        return;
    }


    const top =
        [
            ...safeArray(
                scoringErasData.franchise_seasons
            )
        ]
        .sort(
            (a, b) =>
                Number(
                    b.score_index
                )
                -
                Number(
                    a.score_index
                )
        )
        .slice(
            0,
            7
        );


    container.innerHTML =
        top.map(
            (
                row,
                index
            ) => `

                <div class="scoring-leader-row">

                    <span class="rank-number">
                        ${index + 1}
                    </span>


                    <div class="scoring-leader-name">

                        <strong>
                            ${row.manager}
                        </strong>

                        <span>
                            ${row.season}
                            ·
                            ${formatNumber(
                                row.raw_ppg,
                                1
                            )}
                            PPG
                            ·
                            ${formatNumber(
                                row.ppg_plus,
                                1
                            )}
                            PPG+
                        </span>

                    </div>


                    <strong class="scoring-leader-value">

                        ${formatNumber(
                            row.score_index,
                            1
                        )}

                    </strong>

                </div>
            `
        ).join(
            ""
        );
}



function populateScoringFilters() {

    const seasonSelect =
        document.getElementById(
            "scoringSeasonFilter"
        );


    const franchiseSelect =
        document.getElementById(
            "scoringFranchiseFilter"
        );


    if (
        !seasonSelect
        ||
        !franchiseSelect
    ) {
        return;
    }


    const rows =
        safeArray(
            scoringErasData.franchise_seasons
        );


    const seasons =
        [
            ...new Set(
                rows.map(
                    row =>
                        row.season
                )
            )
        ].sort(
            (a, b) =>
                Number(a)
                -
                Number(b)
        );


    const franchises =
        [
            ...new Set(
                rows.map(
                    row =>
                        row.manager
                )
            )
        ].sort(
            (a, b) =>
                a.localeCompare(
                    b
                )
        );


    seasonSelect.innerHTML =

        '<option value="all">All Seasons</option>'

        +

        seasons.map(
            season =>
                `
                    <option value="${season}">
                        ${season}
                    </option>
                `
        ).join(
            ""
        );


    franchiseSelect.innerHTML =

        '<option value="all">All Franchises</option>'

        +

        franchises.map(
            manager =>
                `
                    <option value="${manager}">
                        ${manager}
                    </option>
                `
        ).join(
            ""
        );
}



function getFilteredScoringRows() {

    const season =
        document.getElementById(
            "scoringSeasonFilter"
        )?.value
        ??
        "all";


    const franchise =
        document.getElementById(
            "scoringFranchiseFilter"
        )?.value
        ??
        "all";


    return safeArray(
        scoringErasData.franchise_seasons
    ).filter(
        row =>

            (
                season === "all"
                ||
                String(
                    row.season
                )
                ===
                season
            )

            &&

            (
                franchise === "all"
                ||
                row.manager
                ===
                franchise
            )
    );
}



function renderScoringTable() {

    const body =
        document.getElementById(
            "scoringBody"
        );


    if (!body) {
        return;
    }


    const rows =
        [
            ...getFilteredScoringRows()
        ];


    rows.sort(
        (a, b) => {

            const key =
                scoringSort.key;


            const aValue =
                key === "manager"

                    ? String(
                        a[key]
                        ??
                        ""
                    )

                    : Number(
                        a[key]
                        ??
                        0
                    );


            const bValue =
                key === "manager"

                    ? String(
                        b[key]
                        ??
                        ""
                    )

                    : Number(
                        b[key]
                        ??
                        0
                    );


            if (
                key === "manager"
            ) {

                const result =
                    aValue.localeCompare(
                        bValue
                    );


                return (
                    scoringSort.direction
                    ===
                    "asc"
                )
                    ? result
                    : -result;
            }


            return (
                scoringSort.direction
                ===
                "asc"
            )
                ? aValue - bValue
                : bValue - aValue;
        }
    );


    body.innerHTML =
        rows.map(
            row => `

                <tr>

                    <td>
                        ${row.season}
                    </td>


                    <td class="franchise-cell">
                        ${row.manager}
                    </td>


                    <td>
                        ${row.games}
                    </td>


                    <td>
                        ${formatNumber(
                            row.points_for,
                            2
                        )}
                    </td>


                    <td>
                        ${formatNumber(
                            row.raw_ppg,
                            2
                        )}
                    </td>


                    <td class="${
                        scoringValueClass(
                            row.ppg_plus,
                            100
                        )
                    }">

                        ${formatNumber(
                            row.ppg_plus,
                            1
                        )}

                    </td>


                    <td class="${
                        scoringValueClass(
                            row.z_score
                        )
                    }">

                        ${
                            Number(
                                row.z_score
                            ) > 0
                                ? "+"
                                : ""
                        }

                        ${formatNumber(
                            row.z_score,
                            2
                        )}

                    </td>


                    <td class="${
                        scoringValueClass(
                            row.score_index,
                            100
                        )
                    }">

                        ${formatNumber(
                            row.score_index,
                            1
                        )}

                    </td>


                    <td>
                        #${row.season_rank}
                    </td>

                </tr>
            `
        ).join(
            ""
        );
}



function setupScoringControls() {

    populateScoringFilters();


    [
        "scoringSeasonFilter",
        "scoringFranchiseFilter",
    ].forEach(
        id => {

            document
                .getElementById(
                    id
                )
                ?.addEventListener(
                    "change",
                    renderScoringTable
                );
        }
    );


    document
        .querySelectorAll(
            "#scoringTable th[data-scoring-sort]"
        )
        .forEach(
            header => {

                header.addEventListener(
                    "click",
                    () => {

                        const key =
                            header.dataset
                                .scoringSort;


                        if (
                            scoringSort.key
                            ===
                            key
                        ) {

                            scoringSort.direction =
                                scoringSort.direction
                                ===
                                "asc"
                                    ? "desc"
                                    : "asc";

                        } else {

                            scoringSort.key =
                                key;


                            scoringSort.direction =
                                (
                                    key === "manager"
                                    ||
                                    key === "season"
                                    ||
                                    key === "season_rank"
                                )
                                    ? "asc"
                                    : "desc";
                        }


                        renderScoringTable();
                    }
                );
            }
        );
}



function renderScoringMethodology() {

    const container =
        document.getElementById(
            "scoringMethodology"
        );


    if (!container) {
        return;
    }


    const methodology =
        scoringErasData.methodology
        ??
        {};


    const keys = [

        "raw_ppg",

        "ppg_plus",

        "z_score",

        "score_index",
    ];


    container.innerHTML =
        keys.map(
            key => {

                const metric =
                    methodology[key];


                if (!metric) {
                    return "";
                }


                return `

                    <article class="card methodology-card">

                        <p class="card-kicker">
                            ${metric.name}
                        </p>


                        <div class="methodology-formula">
                            ${metric.formula}
                        </div>


                        <p>
                            ${metric.description}
                        </p>

                    </article>
                `;
            }
        ).join(
            ""
        );
}



function renderScoringEras() {

    renderScoringSummary();

    renderLeaguePpgChart();

    renderScoringLeaderboard();

    renderScoringTable();

    renderScoringMethodology();
}

initializeDashboard();