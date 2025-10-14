function get(doc, page) {
    const tableWrapper = doc.getElementsByClassName("table-wrapper")[0];
    const tbody = tableWrapper.getElementsByTagName("tbody")[0];
    const rows = [...tbody.getElementsByTagName("tr")];
    const ceres = JSON.parse(localStorage.getItem("ceres")) ?? {};
    const data = rows.map(row=>{
        return [row.getAttribute("success")==="True"?true:false,row.getAttribute("date_str"),row.getAttribute("prefix")]
    })
    const new_ceres = {
        ...ceres,
        ["page" + page]: data
    };
    localStorage.setItem("ceres",JSON.stringify(new_ceres));
    console.log("page" + page);
}

function await2() {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve('Pasaron 2 segundos');
      }, 2000);
    })
}

const pages = 100;
for(var active_page=1;active_page<=pages;active_page++) {
    const url=`https://cci.lbl.gov/ceres/table_all?page=${active_page}`;
    await fetch(`https://cci.lbl.gov/ceres/table_all?page=${active_page}`)
        .then(res=>res.text())
        .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        get(doc, active_page);
    }).then(()=>await2());
}