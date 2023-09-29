1. overall link: https://www.caliper.com/tctraveldemand.htm
2. add load_zone_census_tracts
3. trip generateion (Production and Attraction): 1) corss-classification method  2) Regression Methods  3) Discrete-Choice Methods
4. trip distribution: gravity model
5. mode choice: multinomial logit model, Nested logit model
   src: https://github.com/linhx25/MNLogit-zoo/tree/main ; https://github.com/ryonsd/choice-modeling;
6. traffic assignment: All-or-nothing; STOCH ; Incremental assignment; Capacity Restraint; User  Equilibrium(Frank-Wolf method); Stochastic User Equilibrium (Method of Successive Averages, Sheffi and Powell, 1982; Sheffi, 1985); System optimum Assignment (SO);
7. Advanced Traffic Assignment: Alternative or user-defined volume delay function; HOV assignment; Multi-modal multi-class assignment(MMA);  Volume-Dependent Turning delays and signal opeimization traffic assignment; Combined trip distribution- assignment model; Create volume delay function DDLs
8. Good source: https://github.com/joshchea/python-tdm/tree/master
9. Link performance functions  t = $t_f [1 + \alpha(\dfrac{v}{c})^\beta)] $
