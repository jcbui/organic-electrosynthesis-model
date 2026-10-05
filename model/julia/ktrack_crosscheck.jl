## INDEPENDENT CORROBORATION OF THE TRACKED VALUE, using none of the tracking machinery.
## For this reaction both the no-source floor i_k0 and the regeneration flux that the source adds
## scale as 1/delta -- the floor because it is a diffusion-migration limit, the regeneration
## because it is capped by substrate transport across the same film. Their ratio is therefore
## delta-INDEPENDENT, so i_ec/i_k0 must be the same number in all six reactors. Five of them
## converge by direct ramp + c-control and never touch k-tracking; if the unstirred cell's tracked
## value lands on the same ratio it is corroborated by cells that were solved a different way.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
tr(x)=1e-6*x
sp = [ECSpecies("Br-", -1.0, 2.08e-9, 152.001, -1.0, +1.0),
      ECSpecies("Br2",  0.0, 1.2e-9,  tr(152.),+0.5, -1.0),
      ECSpecies("Sub",  0.0, 6.25e-10, 121.,    0.0, -1.0),
      ECSpecies("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),
      ECSpecies("Na+", +1.0, 1.33e-9, 152.,     0.0,  0.0)]
km = 1e3/1000.0
xk = sqrt(sp[2].D/(km*sp[3].c_bulk))
## deltas and the published EC' values, read straight out of mediated_ec_matrix.csv.
## NOTE ON UNITS: i_ec below is copied from the CSV and is already in mA/cm2, whereas the solver
## returns A/m2. Only i_k0 gets the 0.1 conversion; applying it to i_ec as well divided the ratio
## column by ten on the first run of this script.
cells = [("Unstirred batch",      300.0e-6,      NaN),
         ("Stirred batch",        100.0e-6,      71.26002072290322),
         ("Parallel-plate flow",   86.93461099652019e-6, 81.97299417471426),
         ("Thin-gap microflow",    34.50002323708058e-6, 206.65618939957585),
         ("RDE 1600 rpm",          15.761274893671272e-6, 452.62864406258905),
         ("Rotating cylinder",     14.84333051680979e-6,  480.6081816622069)]
@printf("%-22s %8s %10s %10s %9s\n", "reactor", "d/um", "i_k0", "i_ec", "i_ec/i_k0")
for (nm, d, iec) in cells
    p0 = ECProblem(sp, 2, 3, 0.0, geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/90), 90))
    i_t0 = F_const*sp[1].D*152.0/(abs(sp[1].s)*d)
    i0, lim0, u0s, i0s = solve_ilim_ec(p0; i_start=0.02*i_t0, growth=1.15)
    i_k0 = i0
    if i0s > 0
        ic, limc, _, _, _ = solve_ilim_ec_ccontrol(p0; u0=u0s, i0=i0s)
        if ic > i_k0; i_k0 = ic; end
    end
    if isnan(iec)
        @printf("%-22s %8.1f %10.3f %10s %9s   <- the cell in question\n", nm, d*1e6, i_k0*0.1, "-", "-")
    else
        @printf("%-22s %8.1f %10.3f %10.3f %9.4f\n", nm, d*1e6, i_k0*0.1, iec, iec/(i_k0*0.1))
    end
    flush(stdout)
end
