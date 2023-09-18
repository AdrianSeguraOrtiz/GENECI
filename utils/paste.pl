#!/usr/bin/perl

use strict;

my @csv=();

foreach (@ARGV) {
  my $linenum=0;

  open(F,"<",$_) or die "couldn't open $_ for read: $!\n";

  while (<F>) {
    chomp;
    $csv[$linenum++] .= ";" . $_;
  };

  close(F);
};

foreach (@csv) {
  s/^,//;   # strip leading comma from line
  print $_,"\n";
};