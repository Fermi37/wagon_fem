# Double-Deck Reference Notes

## Source-Grounded Inputs

The following publicly available sources were checked for double-deck passenger-car assumptions:

- Transmashholding product page for the double-deck compartment car model 61-4465: <https://tmholding.ru/products/dvukhetazhnye/dvukhetazhnyy-kupeynyy-vagon-61-4465/>
- Federal Passenger Company 2014 annual report page on double-deck cars: <https://ar2014.fpc.ru/ru/quality_and_safety/double-decker_cars/>
- Federal Passenger Company 2014 annual report page on car types: <https://ar2014.fpc.ru/ru/company/car_types/>
- Federal Passenger Company 2021 annual report page on upgraded rolling stock and the `Vagon 2020` double-deck line: <https://ar2021.fpc.ru/ru/results/rolling-stock/modern>
- Bryansk branch PGUPS lecture PDF with summarized passenger-car dimensions and double-deck characteristics: <https://bryansk.pgups.ru/wp-content/uploads/2024/06/%D0%9A%D1%83%D1%80%D1%81-%D0%BB%D0%B5%D0%BA%D1%86%D0%B8%D0%B9-%D1%81%D0%B6%D0%B0%D1%82%D1%8B%D0%B9.pdf>
- Local assembly drawing for model 61-4465 external appearance. The full path is recorded in [07_body_scheme_illustration.md](07_body_scheme_illustration.md).

## Data Relevant to the Beam Scheme

The Transmashholding page states that the 61-4465 double-deck compartment car is intended for long-distance trains, can operate on electrified and non-electrified lines, has a 40-year service life, a design speed of 160 km/h, and passenger accommodation variants for 64 four-berth compartments or 32 two-berth compartments.

The Federal Passenger Company 2014 annual report identifies the model 61-4465 as a double-deck sleeping compartment car with 64 passengers and a speed of 160 km/h. The same report notes that double-deck trains improve passenger service quality, reduce operating costs, improve labor productivity, and increase infrastructure capacity.

The Federal Passenger Company 2021 annual report states that the `Vagon 2020` double-deck line uses the enlarged `Тпр` rolling-stock gauge according to ГОСТ 9238-2013 to improve upper-berth comfort on the second floor. This supports an explicit `gauge_profile` parameter and a roof-envelope parameter in the generator.

The PGUPS lecture PDF gives engineering dimensions for double-deck passenger cars produced by TVZ: length 26232 mm, bogie base 19000 mm, width 3154 mm, height 5250 mm, design speed 160 km/h, and `Тпр` gauge. It also states that the first-floor level is lowered below the wheelset-axis line and that the compartment and corridor ceiling height is reduced to 2100 mm.

The local assembly drawing confirms the external side elevation of the 61-4465 double-deck body and shows the principal reference dimensions used in the visual scheme: length 26232 mm, bogie base 19000 mm, height 5250 mm, and external width reference 3185 mm. The drawing is treated as the preferred visual reference for the exterior outline and window-level arrangement.

## Parameter Implications

The double-deck generator should include:

- `gauge_profile: Tpr`;
- `length: 26232`;
- `width: 3154`;
- `height_from_rail: 5250` as reference metadata when the rail datum is used;
- `bolster_positions` based on a 19000 mm bogie base when the model uses length over coupler axes;
- `lowered_floor_y` for the central first-floor passenger zone;
- `interdeck_floor_y` for second-floor support beams;
- `roof_ridge_y` or `roof_height` tied to the selected vertical datum;
- `stairwells` near both end zones;
- `sanitary_modules` concentrated near the service end or non-working end according to the selected layout;
- `roof_equipment_zones` and service-equipment load zones.

## Modeling Consequences

The lowered first-floor zone requires transition frames at both boundaries of the lowered-floor interval. These frames should carry vertical load transfer between the lower floor, side walls, center sill, and bolster-zone members.

The interdeck grid acts as a structural diaphragm approximation in the beam-only model. It should contain longitudinal and transverse beams and should connect to side-wall posts at repeated stations.

Stairwells create openings in the interdeck grid. The generator should omit interdeck beams whose midpoint lies inside a stairwell opening and retain stairwell boundary members.

The larger `Тпр` envelope requires roof and side-wall coordinates that differ from ordinary single-deck passenger cars. The generator should store the gauge profile and height assumptions in metadata for traceability.
