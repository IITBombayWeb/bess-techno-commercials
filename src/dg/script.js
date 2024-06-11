document.getElementById('inputForm').addEventListener('submit', function(e) {
    e.preventDefault();

    // Get input values
    const eta = parseFloat(document.getElementById('eta').value);
    const F = parseFloat(document.getElementById('F').value);
    const alpha = parseFloat(document.getElementById('alpha').value);
    const dy = parseFloat(document.getElementById('dy').value);
    const K = parseFloat(document.getElementById('K').value);
    const Rg = parseFloat(document.getElementById('Rg').value);
    const Rd = parseFloat(document.getElementById('Rd').value);
    const Tauo = parseFloat(document.getElementById('Tauo').value);
    const No = parseFloat(document.getElementById('No').value);
    const P_L = parseFloat(document.getElementById('P_L').value);
    const d = parseFloat(document.getElementById('d').value);
    const Lifetime = parseFloat(document.getElementById('lt').value);
    const Annual_O_M_Bat = parseFloat(document.getElementById('OM').value);
    const i = parseFloat(document.getElementById('i').value);


    // Calculate initial investment
    const initialInvestment = F * K * P_L;

    function depreciation(year) {
        return (initialInvestment / (Lifetime*((1+d)**year)));
    }

    function PV_O_M (Annual_O_M, year) {
        return Annual_O_M * (1+i) * (1-((1+i)/(1+d))**year)/(d-i)
    }

    // Calculate annual savings
    function calculateAnnualSavings(year) {
        // Example calculation; replace this with your actual formula
        const outageHoursPerYear = Tauo * No * dy;
        const gridSavings = (outageHoursPerYear * P_L * (Rd - Rg/((1 - alpha)*eta))/((1+d-i)**year)) - PV_O_M(Annual_O_M_Bat, year);
        return gridSavings;
    }




    function constantAnnualSavings() {
        // Example calculation; replace this with your actual formula
        const outageHoursPerYear = Tauo * No * dy;
        const gridSavings = outageHoursPerYear * P_L * (Rd - Rg/((1 - alpha)*eta));
        return gridSavings;
    }

    // Calculate cumulative savings up to a given year
    function calculateCumulativeSavings(upToYear) {
        
        let cumulativeSavings = 0;
        for (let year = 1; year <= upToYear; year++) {
            let annualSavings = calculateAnnualSavings(year);
            cumulativeSavings += annualSavings;
        }
        return cumulativeSavings;
    }

    function CumulativeSavingswithoutd(upToYear) {
        let annualSavings = constantAnnualSavings();
        let cumulativeSavings = 0;
        for (let year = 1; year <= upToYear; year++) {
            
            cumulativeSavings += annualSavings;
        }
        return cumulativeSavings;
    }


    // Data arrays
    const years = [];
    const investments = [];
    const savings = [];
    const const_savings = [];

    // Generate data for 20 years
    for (let year = 0; year <= 30; year++) {
        years.push(year);
        investments.push(initialInvestment);
        savings.push(calculateCumulativeSavings(year));
        const_savings.push(CumulativeSavingswithoutd(year))
    }

    // Plot data using Plotly
    const trace1 = {
        x: years,
        y: investments,
        type: 'scatter',
        mode: 'lines',
        name: 'II',
        line: { color: 'red' }
    };

    const trace2 = {
        x: years,
        y: savings,
        type: 'scatter',
        mode: 'lines',
        name: 'CAS',
        line: { color: 'green' }
    };

    const trace3 = {
        x: years,
        y: const_savings,
        type: 'scatter',
        mode: 'lines',
        name: 'CAS - d',
        line: { color: 'yellow' }

    }

    const data = [trace1, trace2, trace3];

    const layout = {
        title: 'Initial Investment vs Cumulative Annual Savings',
        xaxis: {
            title: 'Years'
        },
        yaxis: {
            title: 'Amount ($)'
        }
    };

    Plotly.newPlot('plot', data, layout);

    // Find intersection point (SPP)
    for (let i = 0; i < years.length; i++) {
        if (savings[i] >= investments[i]) {
            alert(`Payback Period (SPP) is ${years[i]} years`);
            break;
        }
    }
});
