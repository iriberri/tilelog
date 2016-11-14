# Tilelog

## Introduction
Analysis of tile requests from parsed Fastly logs.

This project was developed as the final project for my Bachelor's degree in Telematics Engineering at UC3M through 2015.



## Fastly log example

```
...
<134>2015-03-13T12:59:59Z cache-jfk1026 AshburnLogsS3[39806]: 199.99.94.99 "-" "-" Fri, 13 Mar 2015 12:59:59 GMT GET /username/api/v1/map/username@970195ad@7f0d1c82b45abde157e8c5ff03a2b9fe:1426236941662.6501//5/10/21.png HIT, HIT 200
<134>2015-03-13T12:59:59Z cache-ams4136 AshburnLogsS3[39806]: 99.99.99.99 "-" "-" Fri, 13 Mar 2015 12:59:59 GMT GET /username/api/v1/map/3c69ff53b5b708acc9cffe53ccd0038f:1426003808487.14/11/1052/673.png HIT, HIT 200
<134>2015-03-13T12:59:59Z cache-fra1234 AshburnLogsS3[39806]: 99.99.99.99 "-" "-" Fri, 13 Mar 2015 12:59:59 GMT GET /username/api/v1/map/1c213b3d1ed86e449dfaa2c9d9499da8:1425921407906.75/0/7/63/42.grid.json?callback=grid MISS, HIT 200
...
```


## Attributions
* Basemap sample image: © [OpenStreetMap](http://www.openstreetmap.org/copyright) contributors, © [CARTO](https://carto.com/attributions).
