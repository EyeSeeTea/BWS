function getFilename(doc) {
    return doc.getElementsByClassName("dropdown-item DownloadStuff")[0].href;
}

function await2() {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve('Pasaron 2 segundos');
      }, 2000);
    })
}

const ceres=JSON.parse(localStorage.getItem("ceres"))
const successes=Object.values(ceres).flat().filter(x=>x[0])
const urls=successes.map(([_s,date,entry])=>`https://cci.lbl.gov/ceres/goto_entry/${entry}/${date}/`);

for(var index=0;index<urls.length;index++) {
    await fetch(urls[index])
        .then(res=>res.text())
        .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const filenames=JSON.parse(localStorage.getItem("ceres_filenames"));
        const filename=getFilename(doc);
        const news={...filenames,[index]:filename};
        localStorage.setItem("ceres_filenames",JSON.stringify(news));
    }).then(()=>await2());
}

