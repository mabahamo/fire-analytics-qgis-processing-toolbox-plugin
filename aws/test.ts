import { simulator } from "./wrapper";

simulator({
    inputInstanceFolder: "s3://b9-cell2fire-simulations-development/tif/Portezuelo/",
    outputFolder: "s3://b9-cell2fire-simulations-development/out/test/",
    ignitionPoint: {
        latitude: -36.582051391,
        longitude: -72.419664438
    }
    //NCELL: 4753543
}).then(() => {
    console.log("done");
});